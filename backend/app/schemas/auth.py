from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class GoogleAuthRequest(BaseModel):
    id_token: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
