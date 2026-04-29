from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OptimizerJobCreate(BaseModel):
    dataset_id: UUID
    seed_prompt_template_id: UUID
    candidate_models: list[str] = Field(default_factory=list, min_length=1)
    evaluators: list[str] = ["exact", "semantic", "judge"]
    target_score: float = Field(default=0.85, ge=0, le=1)
    max_budget: float = Field(default=1.0, gt=0)
    max_candidates: int = Field(default=12, ge=1, le=50)
    max_iterations: int = Field(default=3, ge=1, le=10)
    include_adversarial: bool = True


class OptimizerCandidateResponse(BaseModel):
    id: UUID
    job_id: UUID
    prompt_template_id: UUID
    eval_run_id: UUID | None
    model: str
    system_prompt: str
    user_template: str
    iteration: int
    score: float
    cost: float
    latency_ms: float
    passes_target: bool
    pareto_optimal: bool
    pruned: bool
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OptimizerJobResponse(BaseModel):
    id: UUID
    dataset_id: UUID
    seed_prompt_template_id: UUID
    candidate_models: list[str]
    selected_evaluators: list[str]
    target_score: float
    max_budget: float
    max_candidates: int
    max_iterations: int
    include_adversarial: bool
    status: str
    progress: float
    total_spend: float
    best_candidate_id: UUID | None = None
    cheapest_passing_candidate_id: UUID | None = None
    failure_metadata: dict
    created_at: datetime
    updated_at: datetime
    candidates: list[OptimizerCandidateResponse] = []

    model_config = {"from_attributes": True}


class PromoteCandidateResponse(BaseModel):
    prompt_template_id: UUID
    name: str
    version: int
