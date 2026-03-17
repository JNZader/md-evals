"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server configuration via environment variables.

    Required variables will raise a validation error on startup if missing.
    """

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://md_evals:md_evals@localhost:5432/md_evals"

    # --- Auth / JWT ---
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 86400  # 24h

    # --- GitHub OAuth ---
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    STATE_SECRET: str = "change-me-state-secret"

    # --- Frontend ---
    FRONTEND_URL: str = "http://localhost:5173"

    # --- Backend (public URL for OAuth redirect) ---
    BACKEND_URL: str = ""  # If empty, derived from FRONTEND_URL for dev

    # --- Encryption ---
    ENCRYPTION_KEY: str = ""  # 32-byte hex master key for AES-256-GCM

    # --- CORS ---
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
    ]

    # --- Server ---
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = False

    # --- Eval defaults ---
    EVAL_TIMEOUT_MINUTES: int = 10
    MAX_CONCURRENT_EVALS: int = 3
    RATE_LIMIT_PER_HOUR: int = 10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
