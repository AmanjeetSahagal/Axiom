from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ProviderType, User
from app.schemas.provider_keys import ProviderKeyResponse, ProviderKeyStatusResponse, ProviderKeyUpsertRequest
from app.services.provider_keys import delete_provider_key, list_provider_key_statuses, upsert_provider_key

router = APIRouter(prefix="/provider-keys", tags=["provider-keys"])


def _parse_provider(value: str) -> ProviderType:
    try:
        return ProviderType(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {value}") from exc


@router.get("", response_model=list[ProviderKeyStatusResponse])
def get_provider_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_provider_key_statuses(db, current_user.id)


@router.put("", response_model=ProviderKeyResponse, status_code=status.HTTP_200_OK)
def save_provider_key(
    payload: ProviderKeyUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider = _parse_provider(payload.provider)
    if not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")
    return upsert_provider_key(db, current_user.id, provider, payload.api_key.strip())


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
def remove_provider_key(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_provider_key(db, current_user.id, _parse_provider(provider))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
