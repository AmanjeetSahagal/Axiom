import json
from time import perf_counter

import httpx

from app.core.config import settings

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class LLMProviderError(RuntimeError):
    pass


def _gemini_headers() -> dict[str, str]:
    if not settings.gemini_api_key:
        raise LLMProviderError("GEMINI_API_KEY is not configured")
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.gemini_api_key,
    }


def _extract_text(response_json: dict) -> str:
    candidates = response_json.get("candidates", [])
    if not candidates:
        raise LLMProviderError(f"Gemini returned no candidates: {response_json}")
    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [part.get("text", "") for part in parts if part.get("text")]
    return "\n".join(texts).strip()


def _usage_tokens(response_json: dict) -> tuple[int, int]:
    usage = response_json.get("usageMetadata", {})
    return int(usage.get("promptTokenCount", 0)), int(usage.get("candidatesTokenCount", 0))


def call_model(system_prompt: str, user_prompt: str, model: str) -> tuple[str, int, int, int]:
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
    }
    start = perf_counter()
    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{GEMINI_API_BASE}/models/{model}:generateContent",
            headers=_gemini_headers(),
            json=payload,
        )
    if response.status_code >= 400:
        raise LLMProviderError(f"Gemini generateContent failed: {response.text}")
    response_json = response.json()
    text = _extract_text(response_json)
    prompt_tokens, output_tokens = _usage_tokens(response_json)
    latency_ms = int((perf_counter() - start) * 1000)
    return text, latency_ms, prompt_tokens, output_tokens


def embed_text(text: str) -> list[float]:
    payload = {"content": {"parts": [{"text": text}]}}
    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{GEMINI_API_BASE}/models/{settings.gemini_embedding_model}:embedContent",
            headers=_gemini_headers(),
            json=payload,
        )
    if response.status_code >= 400:
        raise LLMProviderError(f"Gemini embedContent failed: {response.text}")
    return response.json().get("embedding", {}).get("values", [])


def judge_response(prompt: str, output: str, expected: str | None, model: str) -> tuple[dict, int, int]:
    rubric = (
        "You are an LLM evaluator. Return strict JSON only with keys "
        'score, hallucination, reason. score must be an integer 1-5. '
        "hallucination must be true or false. reason must be concise."
    )
    payload = {
        "system_instruction": {"parts": [{"text": rubric}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            f"Prompt:\n{prompt}\n\n"
                            f"Model output:\n{output}\n\n"
                            f"Expected output:\n{expected or 'None provided'}\n\n"
                            "Evaluate correctness, groundedness, and hallucination risk."
                        )
                    }
                ],
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    start = perf_counter()
    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{GEMINI_API_BASE}/models/{model}:generateContent",
            headers=_gemini_headers(),
            json=payload,
        )
    if response.status_code >= 400:
        raise LLMProviderError(f"Gemini judge failed: {response.text}")
    response_json = response.json()
    prompt_tokens, output_tokens = _usage_tokens(response_json)
    latency_ms = int((perf_counter() - start) * 1000)
    _ = latency_ms
    return json.loads(_extract_text(response_json)), prompt_tokens, output_tokens
