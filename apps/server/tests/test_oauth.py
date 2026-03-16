"""Tests for GitHub OAuth state generation, validation, and JWT helpers."""

import hashlib
import hmac
import time

from app.services.github_oauth import (
    _base36_decode,
    _base36_encode,
    generate_state,
    validate_state,
)


class TestBase36:
    """Tests for base36 encode/decode helpers."""

    def test_encode_zero(self) -> None:
        assert _base36_encode(0) == "0"

    def test_roundtrip(self) -> None:
        for n in (0, 1, 36, 12345, 1_000_000, int(time.time())):
            encoded = _base36_encode(n)
            assert _base36_decode(encoded) == n

    def test_encode_is_lowercase_alphanumeric(self) -> None:
        encoded = _base36_encode(123456789)
        assert all(c in "0123456789abcdefghijklmnopqrstuvwxyz" for c in encoded)


class TestGenerateState:
    """Tests for HMAC-signed state parameter generation."""

    def test_format_is_timestamp_dot_signature(self) -> None:
        """State has format {base36_ts}.{hex_signature}."""
        state = generate_state()
        parts = state.split(".", maxsplit=1)
        assert len(parts) == 2
        ts_b36, sig = parts
        # Timestamp should be decodable
        ts = _base36_decode(ts_b36)
        assert ts > 0
        # Signature should be a hex string (SHA256 = 64 hex chars)
        assert len(sig) == 64
        assert all(c in "0123456789abcdef" for c in sig)

    def test_state_is_valid_immediately(self) -> None:
        """A freshly generated state should pass validation."""
        state = generate_state()
        assert validate_state(state) is True

    def test_different_calls_produce_same_ts_within_second(self) -> None:
        """Two calls in the same second produce the same timestamp part."""
        state1 = generate_state()
        state2 = generate_state()
        ts1 = state1.split(".")[0]
        ts2 = state2.split(".")[0]
        # They may differ by 1 second if called near a boundary
        diff = abs(_base36_decode(ts1) - _base36_decode(ts2))
        assert diff <= 1


class TestValidateState:
    """Tests for state parameter validation."""

    def test_valid_state_passes(self) -> None:
        """A fresh state should validate successfully."""
        state = generate_state()
        assert validate_state(state) is True

    def test_expired_state_fails(self) -> None:
        """A state older than 5 minutes should fail validation."""
        # Generate a state with a timestamp 6 minutes in the past
        old_ts = int(time.time()) - 360  # 6 minutes ago
        ts_b36 = _base36_encode(old_ts)
        # We need to use the correct secret to sign it
        from app.config import settings

        signature = hmac.new(
            settings.STATE_SECRET.encode(),
            ts_b36.encode(),
            hashlib.sha256,
        ).hexdigest()
        expired_state = f"{ts_b36}.{signature}"
        assert validate_state(expired_state) is False

    def test_tampered_signature_fails(self) -> None:
        """A state with a modified signature should fail validation."""
        state = generate_state()
        ts_b36, sig = state.split(".", maxsplit=1)
        # Flip a hex char in the signature
        bad_char = "1" if sig[0] == "0" else "0"
        tampered_sig = bad_char + sig[1:]
        tampered_state = f"{ts_b36}.{tampered_sig}"
        assert validate_state(tampered_state) is False

    def test_missing_dot_fails(self) -> None:
        """A state without a dot separator should fail."""
        assert validate_state("nodotshere") is False

    def test_empty_string_fails(self) -> None:
        """Empty string should fail validation."""
        assert validate_state("") is False

    def test_invalid_base36_timestamp_fails(self) -> None:
        """A state with an invalid base36 timestamp should fail."""
        assert validate_state("INVALID!!.abcdef1234567890abcdef1234567890abcdef1234567890abcdef12345678") is False

    def test_wrong_secret_fails(self) -> None:
        """A state signed with a different secret should fail."""
        ts = int(time.time())
        ts_b36 = _base36_encode(ts)
        wrong_sig = hmac.new(
            b"wrong-secret",
            ts_b36.encode(),
            hashlib.sha256,
        ).hexdigest()
        bad_state = f"{ts_b36}.{wrong_sig}"
        assert validate_state(bad_state) is False

    def test_state_at_exact_boundary_passes(self) -> None:
        """State exactly at the 5-minute boundary should still pass (within tolerance)."""
        # 299 seconds ago — still within 300s window
        boundary_ts = int(time.time()) - 299
        ts_b36 = _base36_encode(boundary_ts)
        from app.config import settings

        signature = hmac.new(
            settings.STATE_SECRET.encode(),
            ts_b36.encode(),
            hashlib.sha256,
        ).hexdigest()
        boundary_state = f"{ts_b36}.{signature}"
        assert validate_state(boundary_state) is True

    def test_state_just_past_boundary_fails(self) -> None:
        """State at 301 seconds should fail."""
        past_ts = int(time.time()) - 301
        ts_b36 = _base36_encode(past_ts)
        from app.config import settings

        signature = hmac.new(
            settings.STATE_SECRET.encode(),
            ts_b36.encode(),
            hashlib.sha256,
        ).hexdigest()
        past_state = f"{ts_b36}.{signature}"
        assert validate_state(past_state) is False
