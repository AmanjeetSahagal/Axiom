import uuid

from pydantic import ValidationError

from app.models import OptimizationCandidate, OptimizationJob, PromptTemplate
from app.schemas.optimizer import OptimizerJobCreate
from app.services.optimizer import generate_prompt_variants, update_candidate_rankings


def make_candidate(score: float, cost: float, latency_ms: float, passes_target: bool = False) -> OptimizationCandidate:
    return OptimizationCandidate(
        id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        prompt_template_id=uuid.uuid4(),
        model="gemini-2.5-flash",
        system_prompt="system",
        user_template="user",
        score=score,
        cost=cost,
        latency_ms=latency_ms,
        passes_target=passes_target,
    )


def test_update_candidate_rankings_marks_pareto_and_recommendations():
    cheap_passing = make_candidate(0.86, 0.01, 900, passes_target=True)
    expensive_best = make_candidate(0.94, 0.03, 1100, passes_target=True)
    dominated = make_candidate(0.80, 0.04, 1200)
    job = OptimizationJob(id=uuid.uuid4(), target_score=0.85)
    job.candidates = [cheap_passing, expensive_best, dominated]

    update_candidate_rankings(job)

    assert cheap_passing.pareto_optimal is True
    assert expensive_best.pareto_optimal is True
    assert dominated.pareto_optimal is False
    assert dominated.pruned is True
    assert job.best_candidate_id == expensive_best.id
    assert job.cheapest_passing_candidate_id == cheap_passing.id


def test_generate_prompt_variants_preserves_seed_and_bounds_count():
    seed = PromptTemplate(
        name="Seed",
        system_prompt="Answer from context.",
        user_template="Question: {{question}}",
    )

    variants = generate_prompt_variants(seed, max_candidates=4, max_iterations=2)

    assert len(variants) == 4
    assert variants[0]["system_prompt"] == "Answer from context."
    assert variants[0]["user_template"] == "Question: {{question}}"
    assert "not supported" in str(variants[1]["system_prompt"])


def test_optimizer_job_create_validates_budget_and_target():
    try:
        OptimizerJobCreate(
            dataset_id=uuid.uuid4(),
            seed_prompt_template_id=uuid.uuid4(),
            candidate_models=["gemini-2.5-flash"],
            target_score=1.5,
            max_budget=0,
        )
    except ValidationError as exc:
        errors = {tuple(error["loc"]) for error in exc.errors()}
        assert ("target_score",) in errors
        assert ("max_budget",) in errors
    else:
        raise AssertionError("Expected optimizer request validation to fail")
