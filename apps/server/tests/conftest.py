"""Shared test fixtures for the md-evals server test suite."""

import os
import time

import jwt
import pytest

# Ensure test settings before any app imports
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-testing-only")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("STATE_SECRET", "test-state-secret-for-testing-only")
os.environ.setdefault("ENCRYPTION_KEY", "a" * 64)  # 32 bytes hex
os.environ.setdefault("GITHUB_CLIENT_ID", "test-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")


@pytest.fixture()
def jwt_secret() -> str:
    """Return the JWT secret used in tests."""
    return os.environ["JWT_SECRET"]


@pytest.fixture()
def state_secret() -> str:
    """Return the state secret used in tests."""
    return os.environ["STATE_SECRET"]


@pytest.fixture()
def master_key_hex() -> str:
    """Return the hex-encoded master encryption key."""
    return os.environ["ENCRYPTION_KEY"]


@pytest.fixture()
def master_key_bytes(master_key_hex: str) -> bytes:
    """Return the master encryption key as raw bytes."""
    return bytes.fromhex(master_key_hex)


@pytest.fixture()
def sample_user_id() -> str:
    """Return a sample user ID for testing."""
    return "test-user-12345"


@pytest.fixture()
def sample_jwt(jwt_secret: str) -> str:
    """Return a valid JWT token for testing."""
    now = int(time.time())
    payload = {
        "sub": "test-user-12345",
        "github_user_id": 12345,
        "login": "testuser",
        "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        "iat": now,
        "exp": now + 86400,
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


@pytest.fixture()
def expired_jwt(jwt_secret: str) -> str:
    """Return an expired JWT token for testing."""
    now = int(time.time())
    payload = {
        "sub": "test-user-12345",
        "github_user_id": 12345,
        "login": "testuser",
        "avatar_url": "",
        "iat": now - 200000,
        "exp": now - 100000,  # expired 100k seconds ago
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")
