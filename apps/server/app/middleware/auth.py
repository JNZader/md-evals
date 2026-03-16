"""JWT authentication dependency for FastAPI."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status

from app.config import settings


def _extract_token(request: Request) -> str:
    """Extract Bearer token from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "missing_token", "message": "Authorization header is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": "Invalid authorization scheme."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def get_current_user(request: Request) -> dict:
    """FastAPI dependency: decode and validate JWT, return user claims.

    Returns a dict with keys: sub, github_user_id, login, avatar_url.
    Raises 401 on missing/invalid/expired tokens.
    """
    token = _extract_token(request)
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "token_expired", "message": "Token has expired. Please log in again."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": "Invalid token."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# Annotated type for dependency injection in route handlers
CurrentUser = Annotated[dict, Depends(get_current_user)]
