import json
from functools import lru_cache
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials

from app.core.config import settings


@lru_cache(maxsize=1)
def get_firebase_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()
    if settings.firebase_service_account_path:
        service_account = json.loads(
            Path(settings.firebase_service_account_path).read_text(encoding="utf-8")
        )
    elif settings.firebase_service_account_json:
        service_account = json.loads(settings.firebase_service_account_json)
    else:
        raise ValueError(
            "FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_PATH must be configured"
        )
    cred = credentials.Certificate(service_account)
    options = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
    return firebase_admin.initialize_app(cred, options)


def verify_firebase_token(id_token: str) -> dict:
    app = get_firebase_app()
    return auth.verify_id_token(id_token, app=app, check_revoked=False)
