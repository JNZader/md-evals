"""Pydantic request/response schemas for the API."""

from datetime import datetime

from pydantic import BaseModel, Field


# --- Auth ---


class UserInfo(BaseModel):
    """User info returned from JWT validation or auth endpoints."""

    github_id: int
    login: str
    avatar_url: str | None = None


class AuthValidateResponse(BaseModel):
    """Response for POST /auth/validate."""

    user: UserInfo
    exp: int


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


# --- Provider Keys ---


class ProviderKeyCreate(BaseModel):
    """Request to create a provider key."""

    provider: str = Field(..., min_length=1, max_length=50)
    key: str = Field(..., min_length=1)


class ProviderKeyResponse(BaseModel):
    """Response for provider key (masked)."""

    provider: str
    key_hint: str
    is_validated: bool = False
    validated_at: datetime | None = None
    created_at: datetime


class ProviderKeyValidateRequest(BaseModel):
    """Request to validate a provider key without storing."""

    provider: str
    key: str


class ProviderKeyValidateResponse(BaseModel):
    """Response for key validation."""

    valid: bool
    provider: str


# --- Evaluations ---


class EvalRunRequest(BaseModel):
    """Request to launch a new evaluation."""

    name: str = Field(..., min_length=1, max_length=500)
    skill_content: str = Field(..., min_length=1)
    eval_yaml: str = Field(..., min_length=1)
    model: str = "gpt-4o"
    provider: str = "github-models"


class EvalRunResponse(BaseModel):
    """Response for POST /api/eval/run (202 Accepted)."""

    eval_id: str
    status: str = "running"
    created_at: datetime


class EvalDetailResponse(BaseModel):
    """Response for GET /api/eval/{id}."""

    eval_id: str
    title: str
    status: str
    skill_content: str | None = None
    eval_config: dict | None = None
    results: dict | None = None
    cost_metrics: dict | None = None
    context_metrics: dict | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class EvalHistoryItem(BaseModel):
    """Single item in eval history listing."""

    eval_id: str
    title: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None


class EvalHistoryResponse(BaseModel):
    """Paginated eval history response."""

    items: list[EvalHistoryItem]
    total: int
    page: int
    per_page: int
    pages: int


# --- Health ---


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "0.1.0"
    db: str = "unknown"


# --- Errors ---


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str
    message: str
