"""Provider key management routes (CRUD + validation)."""

import logging
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
from app.services.crypto import derive_user_key, encrypt_key, mask_key
from app.services.provider_validator import validate_provider_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/providers", tags=["providers"])


def _get_master_key() -> bytes:
    """Parse the hex-encoded master key from settings."""
    raw = settings.ENCRYPTION_KEY
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "config_error", "message": "Encryption key is not configured."},
        )
    return bytes.fromhex(raw)


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
    """List provider keys for the current user (masked, never full key)."""
    user_id = current_user["sub"]
    result = await db.execute(
        select(ProviderKey).where(ProviderKey.user_id == user_id)
    )
    rows = result.scalars().all()
    return [
        ProviderKeyResponse(
            provider=row.provider,
            key_hint=row.key_hint,
            is_validated=row.is_validated,
            validated_at=row.validated_at,
            created_at=row.created_at,
        )
        for row in rows
    ]


# ---------- Create / Update ----------


@router.post("", response_model=ProviderKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_key(
    body: ProviderKeyCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProviderKeyResponse:
    """Create or update an encrypted provider key.

    The key is validated against the provider's API before storing.
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

    # Encrypt
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
    )


# ---------- Delete ----------


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    provider: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a provider key."""
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
