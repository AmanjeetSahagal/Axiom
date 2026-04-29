from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Dataset, OptimizationCandidate, OptimizationJob, PromptTemplate, User
from app.schemas.optimizer import OptimizerCandidateResponse, OptimizerJobCreate, OptimizerJobResponse, PromoteCandidateResponse
from app.services.optimizer import cancel_optimization_job, create_optimization_job, promote_candidate
from app.tasks.worker import enqueue_optimization_job

router = APIRouter(prefix="/optimizer", tags=["optimizer"])


def get_owned_job_or_404(db: Session, current_user: User, job_id: str | UUID) -> OptimizationJob:
    job = db.execute(
        select(OptimizationJob)
        .join(Dataset, Dataset.id == OptimizationJob.dataset_id)
        .options(
            selectinload(OptimizationJob.candidates),
            selectinload(OptimizationJob.seed_prompt_template),
        )
        .where(OptimizationJob.id == job_id, Dataset.user_id == current_user.id)
    ).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Optimization job not found")
    return job


@router.post("/jobs", response_model=OptimizerJobResponse, status_code=status.HTTP_201_CREATED)
def start_optimizer_job(
    payload: OptimizerJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = db.execute(
        select(Dataset).where(Dataset.id == payload.dataset_id, Dataset.user_id == current_user.id)
    ).scalar_one_or_none()
    seed_prompt = db.execute(
        select(PromptTemplate).where(
            PromptTemplate.id == payload.seed_prompt_template_id,
            PromptTemplate.user_id == current_user.id,
        )
    ).scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not seed_prompt:
        raise HTTPException(status_code=404, detail="Seed prompt not found")

    try:
        job = create_optimization_job(
            db,
            dataset_id=payload.dataset_id,
            seed_prompt_template_id=payload.seed_prompt_template_id,
            candidate_models=payload.candidate_models,
            evaluators=payload.evaluators,
            target_score=payload.target_score,
            max_budget=payload.max_budget,
            max_candidates=payload.max_candidates,
            max_iterations=payload.max_iterations,
            include_adversarial=payload.include_adversarial,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    enqueue_optimization_job(str(job.id))
    return job


@router.get("/jobs", response_model=list[OptimizerJobResponse])
def list_optimizer_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.execute(
            select(OptimizationJob)
            .join(Dataset, Dataset.id == OptimizationJob.dataset_id)
            .options(selectinload(OptimizationJob.candidates))
            .where(Dataset.user_id == current_user.id)
            .order_by(OptimizationJob.created_at.desc())
        )
        .scalars()
        .all()
    )


@router.get("/jobs/{job_id}", response_model=OptimizerJobResponse)
def get_optimizer_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_job_or_404(db, current_user, job_id)


@router.get("/jobs/{job_id}/candidates", response_model=list[OptimizerCandidateResponse])
def list_optimizer_candidates(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_job_or_404(db, current_user, job_id)
    return (
        db.execute(
            select(OptimizationCandidate)
            .where(OptimizationCandidate.job_id == job_id)
            .order_by(OptimizationCandidate.created_at.asc())
        )
        .scalars()
        .all()
    )


@router.post("/jobs/{job_id}/promote", response_model=PromoteCandidateResponse)
def promote_optimizer_candidate(
    job_id: str,
    candidate_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_owned_job_or_404(db, current_user, job_id)
    chosen_candidate_id = candidate_id or job.cheapest_passing_candidate_id or job.best_candidate_id
    if not chosen_candidate_id:
        raise HTTPException(status_code=400, detail="No candidate is available to promote")
    try:
        prompt = promote_candidate(db, job, chosen_candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PromoteCandidateResponse(prompt_template_id=prompt.id, name=prompt.name, version=prompt.version)


@router.post("/jobs/{job_id}/cancel", response_model=OptimizerJobResponse)
def cancel_optimizer_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_owned_job_or_404(db, current_user, job_id)
    return cancel_optimization_job(db, job)
