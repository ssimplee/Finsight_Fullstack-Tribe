from os import getenv


class Settings:
    app_name: str = getenv("APP_NAME", "FinSight API")
    api_v1_prefix: str = getenv("API_V1_PREFIX", "/api/v1")
    database_url: str = getenv("DATABASE_URL", "sqlite:///./finsight.db")
    qwen_api_key: str | None = getenv("QWEN_API_KEY")
    qwen_model: str | None = getenv("QWEN_MODEL")
    rag_provider: str = getenv("RAG_PROVIDER", "local")


settings = Settings()
