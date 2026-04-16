from dataclasses import dataclass
from math import sqrt
import re

from app.services.llm import embed_text, judge_response
from app.services.provider_keys import ProviderKeySet


@dataclass
class EvaluationScore:
    score: float
    passed: bool
    metadata: dict


def _normalize_text(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^\w\s]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def exact_match(output: str, expected: str | None) -> EvaluationScore:
    if not expected:
        return EvaluationScore(score=0.0, passed=False, metadata={"reason": "No expected output"})
    raw_passed = output.strip() == expected.strip()
    normalized_output = _normalize_text(output)
    normalized_expected = _normalize_text(expected)
    normalized_passed = normalized_output == normalized_expected
    return EvaluationScore(
        score=1.0 if normalized_passed else 0.0,
        passed=normalized_passed,
        metadata={
            "raw_match": raw_passed,
            "normalized_match": normalized_passed,
            "normalized_output": normalized_output,
            "normalized_expected": normalized_expected,
        },
    )


def _cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = sqrt(sum(a * a for a in vector_a))
    norm_b = sqrt(sum(b * b for b in vector_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_similarity(output: str, expected: str | None, key_set: ProviderKeySet) -> EvaluationScore:
    if not expected:
        return EvaluationScore(score=0.0, passed=False, metadata={"reason": "No expected output"})
    method = "vector-embedding-cosine"
    output_vector = embed_text(output, key_set)
    expected_vector = embed_text(expected, key_set)
    if not output_vector or not expected_vector:
        output_tokens = set(_normalize_text(output).split())
        expected_tokens = set(_normalize_text(expected).split())
        overlap = len(output_tokens & expected_tokens)
        union = len(output_tokens | expected_tokens) or 1
        score = overlap / union
        method = "token-overlap-jaccard"
    else:
        score = max(0.0, min(1.0, _cosine_similarity(output_vector, expected_vector)))
    return EvaluationScore(score=score, passed=score >= 0.8, metadata={"method": method})


def llm_judge(prompt: str, output: str, expected: str | None, model: str, key_set: ProviderKeySet) -> EvaluationScore:
    judged, prompt_tokens, output_tokens = judge_response(prompt, output, expected, model, key_set)
    raw_score = int(judged.get("score", 1))
    score = max(1, min(5, raw_score))
    hallucination = bool(judged.get("hallucination", False))
    reason = str(judged.get("reason", "No reason provided"))
    return EvaluationScore(
        score=float(score),
        passed=score >= 4 and not hallucination,
        metadata={
            "hallucination": hallucination,
            "reason": reason,
            "judge_model": model,
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
        },
    )
