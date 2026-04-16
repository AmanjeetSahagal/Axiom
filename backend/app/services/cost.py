MODEL_PRICING = {
    "gpt-4.1-mini": {"input": 0.40 / 1_000_000, "output": 1.60 / 1_000_000},
    "gpt-4.1": {"input": 2.00 / 1_000_000, "output": 8.00 / 1_000_000},
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "claude-3.5-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "claude-3.7-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "gemini-2.5-flash": {"input": 0.30 / 1_000_000, "output": 2.50 / 1_000_000},
    "gemini-2.5-flash-lite": {"input": 0.10 / 1_000_000, "output": 0.40 / 1_000_000},
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return 0.0
    return round(
        prompt_tokens * pricing["input"] + completion_tokens * pricing["output"],
        6,
    )
