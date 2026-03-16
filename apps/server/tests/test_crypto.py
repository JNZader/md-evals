"""Tests for AES-256-GCM encryption/decryption and key masking."""

import os

import pytest
from cryptography.exceptions import InvalidTag

from app.services.crypto import decrypt_key, derive_user_key, encrypt_key, mask_key


class TestDeriveUserKey:
    """Tests for HKDF-based per-user key derivation."""

    def test_derives_32_byte_key(self, master_key_bytes: bytes) -> None:
        """Derived key must be exactly 32 bytes (256 bits)."""
        user_key = derive_user_key(master_key_bytes, "user-1")
        assert len(user_key) == 32

    def test_deterministic_for_same_inputs(self, master_key_bytes: bytes) -> None:
        """Same master key + user_id always produces the same derived key."""
        key1 = derive_user_key(master_key_bytes, "user-1")
        key2 = derive_user_key(master_key_bytes, "user-1")
        assert key1 == key2

    def test_different_users_get_different_keys(self, master_key_bytes: bytes) -> None:
        """Different user_ids must produce different derived keys."""
        key1 = derive_user_key(master_key_bytes, "user-1")
        key2 = derive_user_key(master_key_bytes, "user-2")
        assert key1 != key2

    def test_different_master_keys_produce_different_results(self) -> None:
        """Different master keys produce different derived keys for the same user."""
        mk1 = os.urandom(32)
        mk2 = os.urandom(32)
        key1 = derive_user_key(mk1, "same-user")
        key2 = derive_user_key(mk2, "same-user")
        assert key1 != key2


class TestEncryptDecryptRoundtrip:
    """Tests for encrypt → decrypt roundtrip integrity."""

    def test_roundtrip_simple_key(self, master_key_bytes: bytes) -> None:
        """encrypt → decrypt recovers the original plaintext."""
        user_key = derive_user_key(master_key_bytes, "user-1")
        plaintext = "sk-proj-abc123def456ghi789"
        blob = encrypt_key(plaintext, user_key)
        recovered = decrypt_key(blob, user_key)
        assert recovered == plaintext

    def test_roundtrip_empty_string(self, master_key_bytes: bytes) -> None:
        """Roundtrip works for an empty string."""
        user_key = derive_user_key(master_key_bytes, "user-1")
        blob = encrypt_key("", user_key)
        assert decrypt_key(blob, user_key) == ""

    def test_roundtrip_unicode(self, master_key_bytes: bytes) -> None:
        """Roundtrip works for unicode characters."""
        user_key = derive_user_key(master_key_bytes, "user-1")
        plaintext = "sk-clave-con-acentos-y-eñes"
        blob = encrypt_key(plaintext, user_key)
        assert decrypt_key(blob, user_key) == plaintext

    def test_roundtrip_long_key(self, master_key_bytes: bytes) -> None:
        """Roundtrip works for very long API keys."""
        user_key = derive_user_key(master_key_bytes, "user-1")
        plaintext = "sk-" + "a" * 500
        blob = encrypt_key(plaintext, user_key)
        assert decrypt_key(blob, user_key) == plaintext

    def test_different_encryptions_produce_different_blobs(
        self, master_key_bytes: bytes
    ) -> None:
        """Each encrypt call uses a random nonce, producing a different blob."""
        user_key = derive_user_key(master_key_bytes, "user-1")
        plaintext = "sk-proj-abc123"
        blob1 = encrypt_key(plaintext, user_key)
        blob2 = encrypt_key(plaintext, user_key)
        assert blob1 != blob2

    def test_blob_format_nonce_plus_ciphertext(self, master_key_bytes: bytes) -> None:
        """Blob starts with 12-byte nonce and has at least 16 bytes for the tag."""
        user_key = derive_user_key(master_key_bytes, "user-1")
        plaintext = "test"
        blob = encrypt_key(plaintext, user_key)
        # nonce(12) + ciphertext(len(plaintext)) + tag(16)
        assert len(blob) >= 12 + len(plaintext.encode()) + 16

    def test_wrong_key_fails_decryption(self, master_key_bytes: bytes) -> None:
        """Decryption with a wrong key raises InvalidTag."""
        user_key_1 = derive_user_key(master_key_bytes, "user-1")
        user_key_2 = derive_user_key(master_key_bytes, "user-2")
        plaintext = "sk-secret-key"
        blob = encrypt_key(plaintext, user_key_1)
        with pytest.raises(InvalidTag):
            decrypt_key(blob, user_key_2)

    def test_tampered_blob_fails(self, master_key_bytes: bytes) -> None:
        """Modifying the ciphertext blob causes decryption to fail."""
        user_key = derive_user_key(master_key_bytes, "user-1")
        blob = encrypt_key("sk-test-key", user_key)
        # Tamper with a byte in the middle of the ciphertext (after nonce)
        tampered = bytearray(blob)
        tampered[15] ^= 0xFF
        with pytest.raises(InvalidTag):
            decrypt_key(bytes(tampered), user_key)

    def test_truncated_blob_fails(self, master_key_bytes: bytes) -> None:
        """A truncated blob fails to decrypt."""
        user_key = derive_user_key(master_key_bytes, "user-1")
        blob = encrypt_key("sk-test-key", user_key)
        with pytest.raises((InvalidTag, ValueError)):
            decrypt_key(blob[:10], user_key)


class TestMaskKey:
    """Tests for API key masking / hint extraction."""

    def test_normal_key(self) -> None:
        """Normal-length key shows prefix...suffix."""
        assert mask_key("sk-proj-abc123def456") == "sk-...f456"

    def test_short_key_masked(self) -> None:
        """Keys <= 8 chars are fully masked."""
        assert mask_key("short") == "****"
        assert mask_key("12345678") == "****"

    def test_exactly_9_chars_shows_hint(self) -> None:
        """Keys with exactly 9 chars show prefix...suffix."""
        assert mask_key("123456789") == "123...6789"

    def test_very_long_key(self) -> None:
        """Very long keys still show first 3 + last 4."""
        long_key = "sk-" + "x" * 200
        result = mask_key(long_key)
        assert result.startswith("sk-")
        assert result.endswith("xxxx")
        assert "..." in result

    def test_empty_key(self) -> None:
        """Empty key is fully masked."""
        assert mask_key("") == "****"

    def test_single_char_key(self) -> None:
        """Single char key is fully masked."""
        assert mask_key("x") == "****"
