from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.credentials import decrypt_secret, encrypt_secret
from app.models import ProviderType, UserProviderKey


@dataclass
class ProviderKeySet:
    openai: str = ""
    anthropic: str = ""
    gemini: str = ""


def model_provider(model: str) -> ProviderType:
    if model.startswith("gpt-"):
        return ProviderType.openai
    if model.startswith("claude-"):
        return ProviderType.anthropic
    if model.startswith("gemini-"):
        return ProviderType.gemini
    raise ValueError(f"Unsupported generated model: {model}")


def _key_hint(value: str) -> str:
    tail = value[-4:] if len(value) >= 4 else value
    return f"••••{tail}"


def _env_key_for_provider(provider: ProviderType) -> str:
    if provider == ProviderType.openai:
        return settings.openai_api_key
    if provider == ProviderType.anthropic:
        return settings.anthropic_api_key
    if provider == ProviderType.gemini:
        return settings.gemini_api_key
    return ""


def get_provider_key_set(db: Session, user_id: UUID) -> ProviderKeySet:
    rows = db.execute(select(UserProviderKey).where(UserProviderKey.user_id == user_id)).scalars().all()
    key_set = ProviderKeySet(
        openai=settings.openai_api_key,
        anthropic=settings.anthropic_api_key,
        gemini=settings.gemini_api_key,
    )
    for row in rows:
        decrypted = decrypt_secret(row.encrypted_api_key)
        if row.provider == ProviderType.openai:
            key_set.openai = decrypted
        elif row.provider == ProviderType.anthropic:
            key_set.anthropic = decrypted
        elif row.provider == ProviderType.gemini:
            key_set.gemini = decrypted
    return key_set


def provider_available(db: Session, user_id: UUID, provider: ProviderType) -> bool:
    if _env_key_for_provider(provider):
        return True
    row = db.execute(
        select(UserProviderKey).where(
            UserProviderKey.user_id == user_id,
            UserProviderKey.provider == provider,
        )
    ).scalar_one_or_none()
    return row is not None


def list_provider_key_statuses(db: Session, user_id: UUID) -> list[dict]:
    rows = db.execute(select(UserProviderKey).where(UserProviderKey.user_id == user_id)).scalars().all()
    stored = {row.provider: row for row in rows}
    statuses = []
    for provider in ProviderType:
        row = stored.get(provider)
        env_key = _env_key_for_provider(provider)
        statuses.append(
            {
                "provider": provider.value,
                "configured": bool(row or env_key),
                "source": "user" if row else ("environment" if env_key else "missing"),
                "key_hint": row.key_hint if row else (_key_hint(env_key) if env_key else None),
            }
        )
    return statuses


def upsert_provider_key(db: Session, user_id: UUID, provider: ProviderType, api_key: str) -> UserProviderKey:
    row = db.execute(
        select(UserProviderKey).where(
            UserProviderKey.user_id == user_id,
            UserProviderKey.provider == provider,
        )
    ).scalar_one_or_none()
    if not row:
        row = UserProviderKey(user_id=user_id, provider=provider, encrypted_api_key="", key_hint="")
        db.add(row)
    row.encrypted_api_key = encrypt_secret(api_key)
    row.key_hint = _key_hint(api_key)
    db.commit()
    db.refresh(row)
    return row


def delete_provider_key(db: Session, user_id: UUID, provider: ProviderType) -> None:
    row = db.execute(
        select(UserProviderKey).where(
            UserProviderKey.user_id == user_id,
            UserProviderKey.provider == provider,
        )
    ).scalar_one_or_none()
    if row:
        db.delete(row)
        db.commit()
