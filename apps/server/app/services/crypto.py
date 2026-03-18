"""AES-256-GCM encryption for provider API keys.

Uses HKDF to derive per-user keys from a master key, then encrypts/decrypts
with AESGCM. Storage format: nonce(12B) || ciphertext || tag(16B).
"""

import base64
import hashlib
import logging
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

logger = logging.getLogger(__name__)

_NONCE_SIZE = 12  # bytes
_KEY_INFO = b"md-evals-key-encryption"


def normalize_master_key(raw: str) -> bytes:
    """Convert a master-key string (any format) into exactly 32 bytes.

    Accepts:
    1. **Hex string** — 64 hex chars representing 32 bytes (legacy format).
    2. **Base64 string** — base64-encoded blob that decodes to 32 bytes.
    3. **Arbitrary passphrase** — any UTF-8 string; derived into 32 bytes
       via SHA-256 (single-pass, deterministic).

    This makes the ``ENCRYPTION_KEY`` env var forgiving: a randomly generated
    password, a hex string, or a base64 token all work.
    """
    if not raw:
        raise ValueError("ENCRYPTION_KEY is empty")

    # 1. Try hex (must be exactly 64 hex chars → 32 bytes)
    try:
        key = bytes.fromhex(raw)
        if len(key) == 32:
            return key
    except ValueError:
        pass

    # 2. Try base64 (must decode to exactly 32 bytes)
    try:
        key = base64.b64decode(raw, validate=True)
        if len(key) == 32:
            logger.debug("Master key interpreted as base64")
            return key
    except Exception:
        pass

    # 3. Fallback: derive 32 bytes from arbitrary passphrase via SHA-256
    logger.debug("Master key interpreted as passphrase (SHA-256 derivation)")
    return hashlib.sha256(raw.encode("utf-8")).digest()


def derive_user_key(master_key: bytes, user_id: str) -> bytes:
    """Derive a per-user 256-bit encryption key via HKDF.

    Args:
        master_key: 32-byte master key.
        user_id: User identifier used as HKDF salt.

    Returns:
        32-byte derived key.
    """
    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=user_id.encode(),
        info=_KEY_INFO,
    )
    return hkdf.derive(master_key)


def encrypt_key(plaintext: str, encryption_key: bytes) -> bytes:
    """Encrypt an API key with AES-256-GCM.

    Args:
        plaintext: The API key in cleartext.
        encryption_key: 32-byte derived key.

    Returns:
        Bytes in format ``nonce(12) || ciphertext || tag(16)``.
    """
    nonce = os.urandom(_NONCE_SIZE)
    aesgcm = AESGCM(encryption_key)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return nonce + ct  # nonce(12) || ciphertext || tag(16)


def decrypt_key(ciphertext: bytes, encryption_key: bytes) -> str:
    """Decrypt an API key from AES-256-GCM blob.

    Args:
        ciphertext: Bytes in format ``nonce(12) || ciphertext || tag(16)``.
        encryption_key: 32-byte derived key.

    Returns:
        Decrypted API key string.

    Raises:
        cryptography.exceptions.InvalidTag: If decryption fails.
    """
    nonce = ciphertext[:_NONCE_SIZE]
    ct = ciphertext[_NONCE_SIZE:]
    aesgcm = AESGCM(encryption_key)
    return aesgcm.decrypt(nonce, ct, None).decode()


def mask_key(key: str) -> str:
    """Mask an API key for safe display.

    Shows the first 3 characters and last 4 characters, separated by ``...``.
    Returns ``"****"`` for very short keys.

    Args:
        key: Full API key.

    Returns:
        Masked key string, e.g. ``"sk-...a3Fx"``.
    """
    if len(key) <= 8:
        return "****"
    prefix = key[:3]
    suffix = key[-4:]
    return f"{prefix}...{suffix}"
