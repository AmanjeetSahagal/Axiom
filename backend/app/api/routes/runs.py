from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Dataset, EvalResult, EvalRun, PromptTemplate, User
from app.schemas.run import ResultResponse, RunCreate, RunDetailResponse, RunResponse
from app.services.run_service import create_run
from app.tasks.worker import enqueue_run

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def start_run(
    payload: RunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = db.execute(
        select(Dataset).where(Dataset.id == payload.dataset_id, Dataset.user_id == current_user.id)
    ).scalar_one_or_none()
    prompt = db.execute(
        select(PromptTemplate).where(
            PromptTemplate.id == payload.prompt_template_id,
            PromptTemplate.user_id == current_user.id,
        )
    ).scalar_one_or_none()
    if not dataset or not prompt:
        raise HTTPException(status_code=404, detail="Dataset or prompt not found")
    run = create_run(db, payload.dataset_id, payload.prompt_template_id, payload.model)
    enqueue_run(str(run.id))
    return run


@router.get("", response_model=list[RunResponse])
def list_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.execute(
            select(EvalRun)
            .join(Dataset, Dataset.id == EvalRun.dataset_id)
            .where(Dataset.user_id == current_user.id)
            .order_by(EvalRun.created_at.desc())
        )
        .scalars()
        .all()
    )


@router.get("/{run_id}", response_model=RunDetailResponse)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.execute(
        select(EvalRun)
        .join(Dataset, Dataset.id == EvalRun.dataset_id)
        .options(selectinload(EvalRun.results).selectinload(EvalResult.scores))
        .where(EvalRun.id == run_id, Dataset.user_id == current_user.id)
    ).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/results", response_model=list[ResultResponse])
def get_run_results(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = get_run(run_id, db, current_user)
    return run.results
