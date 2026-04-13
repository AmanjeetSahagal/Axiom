from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Axiom API"
    database_url: str
    redis_url: str
    secret_key: str
    access_token_expire_minutes: int = 1440
    algorithm: str = "HS256"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    frontend_url: str = "http://localhost:3000"
    firebase_project_id: str = ""
    firebase_service_account_json: str = ""
    firebase_service_account_path: str = ""


settings = Settings()
