from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProviderKeyStatusResponse(BaseModel):
    provider: str
    configured: bool
    source: str
    key_hint: str | None = None


class ProviderKeyUpsertRequest(BaseModel):
    provider: str
    api_key: str


class ProviderKeyResponse(BaseModel):
    id: UUID
    user_id: UUID
    provider: str
    key_hint: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
