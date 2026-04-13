from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import PromptTemplate, User
from app.schemas.prompt import PromptTemplateCreate, PromptTemplateResponse

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_prompt(
    payload: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    latest = db.execute(
        select(PromptTemplate)
        .where(PromptTemplate.user_id == current_user.id, PromptTemplate.name == payload.name)
        .order_by(PromptTemplate.version.desc())
    ).scalars().first()
    prompt = PromptTemplate(
        user_id=current_user.id,
        name=payload.name,
        system_prompt=payload.system_prompt,
        user_template=payload.user_template,
        version=(latest.version + 1) if latest else 1,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("", response_model=list[PromptTemplateResponse])
def list_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.execute(
            select(PromptTemplate)
            .where(PromptTemplate.user_id == current_user.id)
            .order_by(PromptTemplate.created_at.desc())
        )
        .scalars()
        .all()
    )

