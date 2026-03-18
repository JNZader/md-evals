"""Provider key management routes (CRUD + validation)."""

import logging
import time as _time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.middleware.auth import CurrentUser
from app.models import ProviderKey, get_db
from app.models.schemas import (
    ProviderKeyCreate,
    ProviderKeyResponse,
    ProviderKeyValidateRequest,
    ProviderKeyValidateResponse,
)
from app.services.crypto import derive_user_key, encrypt_key, mask_key, normalize_master_key
from app.services.provider_validator import validate_provider_key
from app.services.session_keys import session_key_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/providers", tags=["providers"])


def _get_master_key() -> bytes:
    """Parse the master key from settings (hex, base64, or passphrase)."""
    raw = settings.ENCRYPTION_KEY
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "config_error", "message": "Encryption key is not configured."},
        )
    return normalize_master_key(raw)


# ---------- Validate (dry-run) ----------


@router.post("/validate", response_model=ProviderKeyValidateResponse)
async def validate_key(
    body: ProviderKeyValidateRequest,
    current_user: CurrentUser,
) -> ProviderKeyValidateResponse:
    """Validate a provider API key without storing it."""
    is_valid, _models = await validate_provider_key(body.provider, body.key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_key",
                "message": f"La API key de {body.provider} es invalida o fue revocada.",
            },
        )
    return ProviderKeyValidateResponse(valid=True, provider=body.provider)


# ---------- List ----------


@router.get("", response_model=list[ProviderKeyResponse])
async def list_keys(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[ProviderKeyResponse]:
    """List provider keys for the current user (masked, never full key).

    Returns both persistent (DB) and session (in-memory) keys, each
    marked with its ``storage`` type.
    """
    user_id = current_user["sub"]

    # 1. Persistent keys from DB
    result = await db.execute(
        select(ProviderKey).where(ProviderKey.user_id == user_id)
    )
    rows = result.scalars().all()

    # Track which providers have persistent keys
    persistent_providers: set[str] = set()
    items: list[ProviderKeyResponse] = []
    for row in rows:
        persistent_providers.add(row.provider)
        items.append(
            ProviderKeyResponse(
                provider=row.provider,
                key_hint=row.key_hint,
                is_validated=row.is_validated,
                validated_at=row.validated_at,
                created_at=row.created_at,
                storage="persistent",
            )
        )

    # 2. Session keys from memory (only add if no persistent key for same provider)
    session_keys = await session_key_store.get_all_keys(user_id)
    now_mono = _time.monotonic()
    now_wall = _time.time()
    for provider, entry in session_keys.items():
        if provider not in persistent_providers:
            # Convert monotonic timestamp to wall-clock for the response
            wall_ts = entry.created_at - now_mono + now_wall
            created = datetime.fromtimestamp(wall_ts, tz=timezone.utc)
            items.append(
                ProviderKeyResponse(
                    provider=provider,
                    key_hint=mask_key(entry.api_key),
                    is_validated=True,
                    validated_at=created,
                    created_at=created,
                    storage="session",
                )
            )

    return items


# ---------- Create / Update ----------


@router.post("", response_model=ProviderKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_key(
    body: ProviderKeyCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProviderKeyResponse:
    """Create or update an encrypted provider key.

    The key is validated against the provider's API before storing.
    When ``storage`` is ``"session"``, the key is kept in memory only.
    """
    user_id = current_user["sub"]

    # Validate the key
    is_valid, _models = await validate_provider_key(body.provider, body.key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_key",
                "message": f"La API key de {body.provider} es invalida o fue revocada.",
            },
        )

    # --- Session-only path: store in memory, skip DB entirely ---
    if body.storage == "session":
        await session_key_store.set_key(
            user_id=user_id,
            provider=body.provider,
            api_key=body.key,
            model_id=None,
        )
        now = datetime.now(timezone.utc)
        logger.info(
            "Session key saved for user=%s provider=%s", user_id, body.provider,
        )
        return ProviderKeyResponse(
            provider=body.provider,
            key_hint=mask_key(body.key),
            is_validated=True,
            validated_at=now,
            created_at=now,
            storage="session",
        )

    # --- Persistent path: encrypt and store in DB ---
    master_key = _get_master_key()
    user_key = derive_user_key(master_key, user_id)
    encrypted = encrypt_key(body.key, user_key)
    hint = mask_key(body.key)
    now = datetime.now(timezone.utc)

    # Upsert — check if key for this provider already exists
    result = await db.execute(
        select(ProviderKey).where(
            ProviderKey.user_id == user_id,
            ProviderKey.provider == body.provider,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.encrypted_api_key = encrypted
        existing.key_hint = hint
        existing.is_validated = True
        existing.validated_at = now
        row = existing
    else:
        row = ProviderKey(
            user_id=user_id,
            provider=body.provider,
            encrypted_api_key=encrypted,
            key_hint=hint,
            is_validated=True,
            validated_at=now,
        )
        db.add(row)

    await db.commit()
    await db.refresh(row)

    logger.info("Provider key saved for user=%s provider=%s", user_id, body.provider)

    return ProviderKeyResponse(
        provider=row.provider,
        key_hint=row.key_hint,
        is_validated=row.is_validated,
        validated_at=row.validated_at,
        created_at=row.created_at,
        storage="persistent",
    )


# ---------- Delete (session — must be registered before /{provider}) ----------


@router.delete("/session/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_key(
    provider: str,
    current_user: CurrentUser,
) -> None:
    """Delete a session-scoped provider key from memory."""
    user_id = current_user["sub"]
    deleted = await session_key_store.delete_key(user_id, provider)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "key_not_found",
                "message": f"No tenes una session key configurada para {provider}.",
            },
        )
    logger.info("Session key deleted for user=%s provider=%s", user_id, provider)


# ---------- Delete (persistent) ----------


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    provider: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a persistent provider key."""
    user_id = current_user["sub"]
    result = await db.execute(
        select(ProviderKey).where(
            ProviderKey.user_id == user_id,
            ProviderKey.provider == provider,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "key_not_found",
                "message": f"No tenes una key configurada para {provider}.",
            },
        )
    await db.delete(row)
    await db.commit()
    logger.info("Provider key deleted for user=%s provider=%s", user_id, provider)
