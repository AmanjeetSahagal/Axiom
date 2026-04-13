from dataclasses import dataclass
from math import sqrt

from app.services.llm import embed_text, judge_response


@dataclass
class EvaluationScore:
    score: float
    passed: bool
    metadata: dict


def exact_match(output: str, expected: str | None) -> EvaluationScore:
    if not expected:
        return EvaluationScore(score=0.0, passed=False, metadata={"reason": "No expected output"})
    passed = output.strip() == expected.strip()
    return EvaluationScore(score=1.0 if passed else 0.0, passed=passed, metadata={})


def _cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = sqrt(sum(a * a for a in vector_a))
    norm_b = sqrt(sum(b * b for b in vector_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_similarity(output: str, expected: str | None) -> EvaluationScore:
    if not expected:
        return EvaluationScore(score=0.0, passed=False, metadata={"reason": "No expected output"})
    score = max(0.0, min(1.0, _cosine_similarity(embed_text(output), embed_text(expected))))
    return EvaluationScore(score=score, passed=score >= 0.8, metadata={"method": "gemini-embedding-cosine"})


def llm_judge(prompt: str, output: str, expected: str | None, model: str) -> EvaluationScore:
    judged, prompt_tokens, output_tokens = judge_response(prompt, output, expected, model)
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
