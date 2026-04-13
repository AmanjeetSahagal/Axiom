from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.firebase import verify_firebase_token
from app.core.security import create_access_token
from app.db.session import get_db
from app.models import User
from app.schemas.auth import AuthResponse, GoogleAuthRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=AuthResponse, status_code=status.HTTP_200_OK)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        claims = verify_firebase_token(payload.id_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {exc}") from exc

    email = claims.get("email")
    email_verified = claims.get("email_verified", False)
    if not email or not email_verified:
        raise HTTPException(status_code=401, detail="Verified Google email is required")

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        user = User(email=email, password_hash="")
        db.add(user)
        db.commit()
        db.refresh(user)
    return AuthResponse(access_token=create_access_token(str(user.id)), user=user)
