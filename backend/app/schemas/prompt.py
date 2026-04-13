from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PromptTemplateCreate(BaseModel):
    name: str
    system_prompt: str
    user_template: str


class PromptTemplateResponse(PromptTemplateCreate):
    id: UUID
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}

