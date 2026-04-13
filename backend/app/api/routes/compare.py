from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Dataset, EvalRun, User
from app.schemas.run import CompareRequest, CompareResponse
from app.services.run_service import compare_runs

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
def compare(
    payload: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    owned_run_ids = {
        run_id
        for run_id in db.execute(
            select(EvalRun.id)
            .join(Dataset, Dataset.id == EvalRun.dataset_id)
            .where(
                Dataset.user_id == current_user.id,
                EvalRun.id.in_([payload.baseline_run_id, payload.candidate_run_id]),
            )
        )
        .scalars()
        .all()
    }
    if payload.baseline_run_id not in owned_run_ids or payload.candidate_run_id not in owned_run_ids:
        raise HTTPException(status_code=404, detail="Run not found")
    return compare_runs(db, payload.baseline_run_id, payload.candidate_run_id)
