"""Tests for Pydantic request/response schemas validation."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    AuthValidateResponse,
    ErrorResponse,
    EvalDetailResponse,
    EvalHistoryItem,
    EvalHistoryResponse,
    EvalRunRequest,
    EvalRunResponse,
    HealthResponse,
    ProviderKeyCreate,
    ProviderKeyResponse,
    ProviderKeyValidateRequest,
    ProviderKeyValidateResponse,
    TokenResponse,
    UserInfo,
)


class TestUserInfo:
    """Tests for UserInfo schema."""

    def test_valid_user_info(self) -> None:
        user = UserInfo(github_id=12345, login="testuser", avatar_url="https://example.com/avatar.png")
        assert user.github_id == 12345
        assert user.login == "testuser"
        assert user.avatar_url == "https://example.com/avatar.png"

    def test_avatar_url_optional(self) -> None:
        user = UserInfo(github_id=1, login="u")
        assert user.avatar_url is None

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            UserInfo()  # type: ignore[call-arg]

    def test_missing_login(self) -> None:
        with pytest.raises(ValidationError):
            UserInfo(github_id=1)  # type: ignore[call-arg]


class TestAuthValidateResponse:
    """Tests for AuthValidateResponse schema."""

    def test_valid_response(self) -> None:
        resp = AuthValidateResponse(
            user=UserInfo(github_id=1, login="u"),
            exp=1700000000,
        )
        assert resp.exp == 1700000000
        assert resp.user.login == "u"


class TestTokenResponse:
    """Tests for TokenResponse schema."""

    def test_defaults(self) -> None:
        token = TokenResponse(access_token="eyJ...")
        assert token.token_type == "bearer"
        assert token.expires_in == 86400

    def test_custom_values(self) -> None:
        token = TokenResponse(access_token="abc", token_type="mac", expires_in=3600)
        assert token.token_type == "mac"
        assert token.expires_in == 3600


class TestProviderKeyCreate:
    """Tests for ProviderKeyCreate request schema."""

    def test_valid_create(self) -> None:
        req = ProviderKeyCreate(provider="openai", key="sk-abc123")
        assert req.provider == "openai"
        assert req.key == "sk-abc123"

    def test_provider_min_length(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProviderKeyCreate(provider="", key="sk-abc")
        assert "provider" in str(exc_info.value)

    def test_provider_max_length(self) -> None:
        with pytest.raises(ValidationError):
            ProviderKeyCreate(provider="x" * 51, key="sk-abc")

    def test_key_min_length(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            ProviderKeyCreate(provider="openai", key="")
        assert "key" in str(exc_info.value)

    def test_missing_fields(self) -> None:
        with pytest.raises(ValidationError):
            ProviderKeyCreate()  # type: ignore[call-arg]


class TestProviderKeyResponse:
    """Tests for ProviderKeyResponse schema."""

    def test_valid_response(self) -> None:
        now = datetime.now(timezone.utc)
        resp = ProviderKeyResponse(
            provider="openai",
            key_hint="sk-...a3Fx",
            is_validated=True,
            validated_at=now,
            created_at=now,
        )
        assert resp.provider == "openai"
        assert resp.is_validated is True

    def test_defaults(self) -> None:
        now = datetime.now(timezone.utc)
        resp = ProviderKeyResponse(
            provider="anthropic",
            key_hint="****",
            created_at=now,
        )
        assert resp.is_validated is False
        assert resp.validated_at is None


class TestProviderKeyValidate:
    """Tests for key validation request/response schemas."""

    def test_validate_request(self) -> None:
        req = ProviderKeyValidateRequest(provider="openai", key="sk-test")
        assert req.provider == "openai"

    def test_validate_response(self) -> None:
        resp = ProviderKeyValidateResponse(valid=True, provider="openai")
        assert resp.valid is True


class TestEvalRunRequest:
    """Tests for EvalRunRequest schema."""

    def test_valid_request(self) -> None:
        req = EvalRunRequest(
            name="Test Eval",
            skill_content="# SKILL.md\nSome content",
            eval_yaml="name: test\ntests:\n  - name: t1",
        )
        assert req.name == "Test Eval"
        assert req.model == "gpt-4o"  # default
        assert req.provider == "github-models"  # default

    def test_custom_model_and_provider(self) -> None:
        req = EvalRunRequest(
            name="Custom",
            skill_content="content",
            eval_yaml="yaml",
            model="claude-sonnet-4-20250514",
            provider="anthropic",
        )
        assert req.model == "claude-sonnet-4-20250514"
        assert req.provider == "anthropic"

    def test_name_min_length(self) -> None:
        with pytest.raises(ValidationError):
            EvalRunRequest(name="", skill_content="x", eval_yaml="y")

    def test_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            EvalRunRequest(name="x" * 501, skill_content="x", eval_yaml="y")

    def test_skill_content_required(self) -> None:
        with pytest.raises(ValidationError):
            EvalRunRequest(name="test", skill_content="", eval_yaml="y")

    def test_eval_yaml_required(self) -> None:
        with pytest.raises(ValidationError):
            EvalRunRequest(name="test", skill_content="x", eval_yaml="")


class TestEvalRunResponse:
    """Tests for EvalRunResponse schema."""

    def test_valid_response(self) -> None:
        now = datetime.now(timezone.utc)
        resp = EvalRunResponse(eval_id="abc-123", status="running", created_at=now)
        assert resp.status == "running"
        assert resp.eval_id == "abc-123"


class TestEvalDetailResponse:
    """Tests for EvalDetailResponse schema."""

    def test_minimal_response(self) -> None:
        now = datetime.now(timezone.utc)
        resp = EvalDetailResponse(
            eval_id="abc",
            title="My Eval",
            status="completed",
            created_at=now,
        )
        assert resp.skill_content is None
        assert resp.eval_config is None
        assert resp.results is None

    def test_full_response(self) -> None:
        now = datetime.now(timezone.utc)
        resp = EvalDetailResponse(
            eval_id="abc",
            title="Full Eval",
            status="completed",
            skill_content="# Skill",
            eval_config={"tests": []},
            results={"summary": {"total": 5}},
            cost_metrics={"total_cost": 0.01},
            context_metrics={"utilization": 0.5},
            created_at=now,
            completed_at=now,
        )
        assert resp.results is not None
        assert resp.cost_metrics is not None


class TestEvalHistory:
    """Tests for eval history schemas."""

    def test_history_item(self) -> None:
        now = datetime.now(timezone.utc)
        item = EvalHistoryItem(
            eval_id="abc",
            title="Eval 1",
            status="completed",
            created_at=now,
        )
        assert item.completed_at is None

    def test_history_response(self) -> None:
        now = datetime.now(timezone.utc)
        resp = EvalHistoryResponse(
            items=[
                EvalHistoryItem(eval_id="1", title="E1", status="completed", created_at=now),
                EvalHistoryItem(eval_id="2", title="E2", status="failed", created_at=now),
            ],
            total=50,
            page=1,
            per_page=20,
            pages=3,
        )
        assert len(resp.items) == 2
        assert resp.total == 50

    def test_empty_history(self) -> None:
        resp = EvalHistoryResponse(items=[], total=0, page=1, per_page=20, pages=1)
        assert len(resp.items) == 0


class TestHealthResponse:
    """Tests for HealthResponse schema."""

    def test_defaults(self) -> None:
        health = HealthResponse()
        assert health.status == "ok"
        assert health.version == "0.1.0"
        assert health.db == "unknown"

    def test_custom(self) -> None:
        health = HealthResponse(status="ok", version="1.0.0", db="connected")
        assert health.db == "connected"


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_error_response(self) -> None:
        err = ErrorResponse(error="invalid_key", message="Key is invalid.")
        assert err.error == "invalid_key"

    def test_missing_fields(self) -> None:
        with pytest.raises(ValidationError):
            ErrorResponse()  # type: ignore[call-arg]
