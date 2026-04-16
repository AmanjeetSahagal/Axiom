import json
import time
from time import perf_counter

import httpx

from app.core.config import settings
from app.models import ProviderType
from app.services.provider_keys import ProviderKeySet, model_provider

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
OPENAI_API_BASE = "https://api.openai.com/v1"
ANTHROPIC_API_BASE = "https://api.anthropic.com/v1"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_PROVIDER_RETRIES = 3
BASE_RETRY_DELAY_SECONDS = 1.0


class LLMProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        provider: str,
        status_code: int | None = None,
        retryable: bool = False,
        provider_message: str | None = None,
        provider_status: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable
        self.provider_message = provider_message
        self.provider_status = provider_status


def _extract_error_fields(response: httpx.Response) -> tuple[str, str | None]:
    try:
        payload = response.json()
    except Exception:
        text = response.text.strip() or f"HTTP {response.status_code}"
        return text, None

    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or response.text.strip() or f"HTTP {response.status_code}"
        provider_status = error.get("status")
        return str(message), str(provider_status) if provider_status else None
    return response.text.strip() or f"HTTP {response.status_code}", None


def _post_with_retries(url: str, headers: dict[str, str], payload: dict, *, provider: str) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_PROVIDER_RETRIES + 1):
        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(url, headers=headers, json=payload)
            if response.status_code < 400:
                return response.json()
            if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_PROVIDER_RETRIES:
                time.sleep(BASE_RETRY_DELAY_SECONDS * (2**attempt))
                continue
            provider_message, provider_status = _extract_error_fields(response)
            message = f"{provider.title()} request failed"
            if response.status_code:
                message += f" ({response.status_code}"
                if provider_status:
                    message += f" {provider_status}"
                message += ")"
            message += f": {provider_message}"
            raise LLMProviderError(
                message,
                provider=provider,
                status_code=response.status_code,
                retryable=response.status_code in RETRYABLE_STATUS_CODES,
                provider_message=provider_message,
                provider_status=provider_status,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_error = exc
            if attempt < MAX_PROVIDER_RETRIES:
                time.sleep(BASE_RETRY_DELAY_SECONDS * (2**attempt))
                continue
            raise LLMProviderError(
                f"{provider.title()} request failed after retries: {exc}",
                provider=provider,
                retryable=True,
                provider_message=str(exc),
            ) from exc
    raise LLMProviderError(
        f"{provider.title()} request failed after retries: {last_error}",
        provider=provider,
        retryable=True,
        provider_message=str(last_error) if last_error else None,
    )


def provider_error_metadata(exc: Exception) -> dict:
    if isinstance(exc, LLMProviderError):
        return {
            "provider": exc.provider,
            "status_code": exc.status_code,
            "retryable": exc.retryable,
            "provider_message": exc.provider_message,
            "provider_status": exc.provider_status,
        }
    return {}


def _require_key(provider: ProviderType, key_set: ProviderKeySet) -> str:
    if provider == ProviderType.openai and key_set.openai:
        return key_set.openai
    if provider == ProviderType.anthropic and key_set.anthropic:
        return key_set.anthropic
    if provider == ProviderType.gemini and key_set.gemini:
        return key_set.gemini
    raise LLMProviderError(f"No API key configured for {provider.value}")


def _extract_gemini_text(response_json: dict) -> str:
    candidates = response_json.get("candidates", [])
    if not candidates:
        raise LLMProviderError(f"Gemini returned no candidates: {response_json}")
    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [part.get("text", "") for part in parts if part.get("text")]
    return "\n".join(texts).strip()


def _extract_openai_text(response_json: dict) -> str:
    choices = response_json.get("choices", [])
    if not choices:
        raise LLMProviderError(f"OpenAI returned no choices: {response_json}")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        return "\n".join(block.get("text", "") for block in content if isinstance(block, dict)).strip()
    return str(content).strip()


def _extract_anthropic_text(response_json: dict) -> str:
    content = response_json.get("content", [])
    texts = [block.get("text", "") for block in content if isinstance(block, dict) and block.get("type") == "text"]
    text = "\n".join(texts).strip()
    if not text:
        raise LLMProviderError(f"Anthropic returned no text blocks: {response_json}")
    return text


def _parse_json_text(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


def _gemini_usage_tokens(response_json: dict) -> tuple[int, int]:
    usage = response_json.get("usageMetadata", {})
    return int(usage.get("promptTokenCount", 0)), int(usage.get("candidatesTokenCount", 0))


def _openai_usage_tokens(response_json: dict) -> tuple[int, int]:
    usage = response_json.get("usage", {})
    return int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))


def _anthropic_usage_tokens(response_json: dict) -> tuple[int, int]:
    usage = response_json.get("usage", {})
    return int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0))


def _call_gemini(system_prompt: str, user_prompt: str, model: str, api_key: str) -> tuple[str, int, int, int]:
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
    }
    start = perf_counter()
    response_json = _post_with_retries(
        f"{GEMINI_API_BASE}/models/{model}:generateContent",
        {"Content-Type": "application/json", "x-goog-api-key": api_key},
        payload,
        provider="gemini",
    )
    text = _extract_gemini_text(response_json)
    prompt_tokens, output_tokens = _gemini_usage_tokens(response_json)
    latency_ms = int((perf_counter() - start) * 1000)
    return text, latency_ms, prompt_tokens, output_tokens


def _call_openai(system_prompt: str, user_prompt: str, model: str, api_key: str) -> tuple[str, int, int, int]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    start = perf_counter()
    response_json = _post_with_retries(
        f"{OPENAI_API_BASE}/chat/completions",
        {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        payload,
        provider="openai",
    )
    text = _extract_openai_text(response_json)
    prompt_tokens, output_tokens = _openai_usage_tokens(response_json)
    latency_ms = int((perf_counter() - start) * 1000)
    return text, latency_ms, prompt_tokens, output_tokens


def _call_anthropic(system_prompt: str, user_prompt: str, model: str, api_key: str) -> tuple[str, int, int, int]:
    payload = {
        "model": model,
        "system": system_prompt,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    start = perf_counter()
    response_json = _post_with_retries(
        f"{ANTHROPIC_API_BASE}/messages",
        {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        payload,
        provider="anthropic",
    )
    text = _extract_anthropic_text(response_json)
    prompt_tokens, output_tokens = _anthropic_usage_tokens(response_json)
    latency_ms = int((perf_counter() - start) * 1000)
    return text, latency_ms, prompt_tokens, output_tokens


def call_model(system_prompt: str, user_prompt: str, model: str, key_set: ProviderKeySet) -> tuple[str, int, int, int]:
    provider = model_provider(model)
    api_key = _require_key(provider, key_set)
    if provider == ProviderType.gemini:
        return _call_gemini(system_prompt, user_prompt, model, api_key)
    if provider == ProviderType.openai:
        return _call_openai(system_prompt, user_prompt, model, api_key)
    if provider == ProviderType.anthropic:
        return _call_anthropic(system_prompt, user_prompt, model, api_key)
    raise LLMProviderError(f"Unsupported provider for model {model}")


def embed_text(text: str, key_set: ProviderKeySet) -> list[float]:
    if key_set.openai:
        response_json = _post_with_retries(
            f"{OPENAI_API_BASE}/embeddings",
            {"Content-Type": "application/json", "Authorization": f"Bearer {key_set.openai}"},
            {"model": settings.openai_embedding_model, "input": text},
            provider="openai",
        )
        data = response_json.get("data", [])
        if data:
            return data[0].get("embedding", [])
    if key_set.gemini:
        response_json = _post_with_retries(
            f"{GEMINI_API_BASE}/models/{settings.gemini_embedding_model}:embedContent",
            {"Content-Type": "application/json", "x-goog-api-key": key_set.gemini},
            {"content": {"parts": [{"text": text}]}},
            provider="gemini",
        )
        return response_json.get("embedding", {}).get("values", [])
    return []


def judge_response(prompt: str, output: str, expected: str | None, model: str, key_set: ProviderKeySet) -> tuple[dict, int, int]:
    rubric = (
        "You are an LLM evaluator. Return strict JSON only with keys "
        'score, hallucination, reason. score must be an integer 1-5. '
        "hallucination must be true or false. reason must be concise."
    )
    provider = model_provider(model)
    api_key = _require_key(provider, key_set)
    judge_prompt = (
        f"Prompt:\n{prompt}\n\n"
        f"Model output:\n{output}\n\n"
        f"Expected output:\n{expected or 'None provided'}\n\n"
        "Evaluate correctness, groundedness, and hallucination risk."
    )

    if provider == ProviderType.gemini:
        response_json = _post_with_retries(
            f"{GEMINI_API_BASE}/models/{model}:generateContent",
            {"Content-Type": "application/json", "x-goog-api-key": api_key},
            {
                "system_instruction": {"parts": [{"text": rubric}]},
                "contents": [{"role": "user", "parts": [{"text": judge_prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            },
            provider="gemini",
        )
        prompt_tokens, output_tokens = _gemini_usage_tokens(response_json)
        return _parse_json_text(_extract_gemini_text(response_json)), prompt_tokens, output_tokens

    if provider == ProviderType.openai:
        response_json = _post_with_retries(
            f"{OPENAI_API_BASE}/chat/completions",
            {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": rubric},
                    {"role": "user", "content": judge_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
            provider="openai",
        )
        prompt_tokens, output_tokens = _openai_usage_tokens(response_json)
        return _parse_json_text(_extract_openai_text(response_json)), prompt_tokens, output_tokens

    if provider == ProviderType.anthropic:
        response_json = _post_with_retries(
            f"{ANTHROPIC_API_BASE}/messages",
            {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            {
                "model": model,
                "system": f"{rubric} Output JSON only.",
                "max_tokens": 512,
                "messages": [{"role": "user", "content": judge_prompt}],
            },
            provider="anthropic",
        )
        prompt_tokens, output_tokens = _anthropic_usage_tokens(response_json)
        return _parse_json_text(_extract_anthropic_text(response_json)), prompt_tokens, output_tokens

    raise LLMProviderError(f"Unsupported provider for model {model}")
