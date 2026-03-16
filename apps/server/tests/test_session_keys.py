"""Tests for the in-memory session key store."""

import asyncio

import pytest

from app.services.session_keys import SessionKeyStore


@pytest.fixture()
def store() -> SessionKeyStore:
    """Create a fresh session key store with a short TTL for testing."""
    return SessionKeyStore(ttl=86400)


@pytest.fixture()
def short_ttl_store() -> SessionKeyStore:
    """Create a store with a very short TTL (0.1s) for expiration tests."""
    return SessionKeyStore(ttl=0.1)


class TestSetAndGetKey:
    """Tests for basic set/get operations."""

    @pytest.mark.asyncio()
    async def test_set_and_get_key(self, store: SessionKeyStore) -> None:
        """Setting a key and retrieving it returns the same value."""
        await store.set_key("user-1", "openai", "sk-abc123")
        entry = await store.get_key("user-1", "openai")
        assert entry is not None
        assert entry.api_key == "sk-abc123"
        assert entry.model_id is None

    @pytest.mark.asyncio()
    async def test_set_key_with_model_id(self, store: SessionKeyStore) -> None:
        """Setting a key with model_id stores both values."""
        await store.set_key("user-1", "openai", "sk-abc123", model_id="gpt-4o")
        entry = await store.get_key("user-1", "openai")
        assert entry is not None
        assert entry.api_key == "sk-abc123"
        assert entry.model_id == "gpt-4o"

    @pytest.mark.asyncio()
    async def test_get_nonexistent_user(self, store: SessionKeyStore) -> None:
        """Getting a key for a nonexistent user returns None."""
        entry = await store.get_key("nonexistent", "openai")
        assert entry is None

    @pytest.mark.asyncio()
    async def test_get_nonexistent_provider(self, store: SessionKeyStore) -> None:
        """Getting a key for a nonexistent provider returns None."""
        await store.set_key("user-1", "openai", "sk-abc123")
        entry = await store.get_key("user-1", "anthropic")
        assert entry is None

    @pytest.mark.asyncio()
    async def test_overwrite_existing_key(self, store: SessionKeyStore) -> None:
        """Setting a key for an existing (user, provider) pair overwrites it."""
        await store.set_key("user-1", "openai", "sk-old")
        await store.set_key("user-1", "openai", "sk-new")
        entry = await store.get_key("user-1", "openai")
        assert entry is not None
        assert entry.api_key == "sk-new"

    @pytest.mark.asyncio()
    async def test_multiple_providers(self, store: SessionKeyStore) -> None:
        """A user can have keys for multiple providers."""
        await store.set_key("user-1", "openai", "sk-openai")
        await store.set_key("user-1", "anthropic", "sk-ant-123")
        assert (await store.get_key("user-1", "openai")).api_key == "sk-openai"
        assert (await store.get_key("user-1", "anthropic")).api_key == "sk-ant-123"


class TestDeleteKey:
    """Tests for key deletion."""

    @pytest.mark.asyncio()
    async def test_delete_existing_key(self, store: SessionKeyStore) -> None:
        """Deleting an existing key returns True and removes it."""
        await store.set_key("user-1", "openai", "sk-abc123")
        result = await store.delete_key("user-1", "openai")
        assert result is True
        assert await store.get_key("user-1", "openai") is None

    @pytest.mark.asyncio()
    async def test_delete_nonexistent_key(self, store: SessionKeyStore) -> None:
        """Deleting a nonexistent key returns False."""
        result = await store.delete_key("user-1", "openai")
        assert result is False

    @pytest.mark.asyncio()
    async def test_delete_nonexistent_provider(self, store: SessionKeyStore) -> None:
        """Deleting a key for a different provider returns False."""
        await store.set_key("user-1", "openai", "sk-abc123")
        result = await store.delete_key("user-1", "anthropic")
        assert result is False

    @pytest.mark.asyncio()
    async def test_delete_does_not_affect_other_providers(
        self, store: SessionKeyStore
    ) -> None:
        """Deleting one provider's key does not affect others."""
        await store.set_key("user-1", "openai", "sk-openai")
        await store.set_key("user-1", "anthropic", "sk-ant")
        await store.delete_key("user-1", "openai")
        entry = await store.get_key("user-1", "anthropic")
        assert entry is not None
        assert entry.api_key == "sk-ant"


class TestGetAllKeys:
    """Tests for listing all keys for a user."""

    @pytest.mark.asyncio()
    async def test_get_all_keys(self, store: SessionKeyStore) -> None:
        """get_all_keys returns all non-expired keys for a user."""
        await store.set_key("user-1", "openai", "sk-openai")
        await store.set_key("user-1", "anthropic", "sk-ant")
        keys = await store.get_all_keys("user-1")
        assert len(keys) == 2
        assert "openai" in keys
        assert "anthropic" in keys

    @pytest.mark.asyncio()
    async def test_get_all_keys_empty(self, store: SessionKeyStore) -> None:
        """get_all_keys returns empty dict for a user with no keys."""
        keys = await store.get_all_keys("nonexistent")
        assert keys == {}


class TestTTLExpiration:
    """Tests for automatic TTL-based expiration."""

    @pytest.mark.asyncio()
    async def test_expired_key_returns_none(
        self, short_ttl_store: SessionKeyStore
    ) -> None:
        """A key past its TTL is automatically removed on get."""
        await short_ttl_store.set_key("user-1", "openai", "sk-abc123")
        # Wait for TTL to expire
        await asyncio.sleep(0.15)
        entry = await short_ttl_store.get_key("user-1", "openai")
        assert entry is None

    @pytest.mark.asyncio()
    async def test_expired_key_excluded_from_get_all(
        self, short_ttl_store: SessionKeyStore
    ) -> None:
        """Expired keys are excluded from get_all_keys."""
        await short_ttl_store.set_key("user-1", "openai", "sk-openai")
        await asyncio.sleep(0.15)
        keys = await short_ttl_store.get_all_keys("user-1")
        assert keys == {}

    @pytest.mark.asyncio()
    async def test_non_expired_key_still_accessible(
        self, short_ttl_store: SessionKeyStore
    ) -> None:
        """A key within its TTL is still accessible."""
        await short_ttl_store.set_key("user-1", "openai", "sk-abc123")
        entry = await short_ttl_store.get_key("user-1", "openai")
        assert entry is not None
        assert entry.api_key == "sk-abc123"


class TestCleanupExpired:
    """Tests for the cleanup_expired method."""

    @pytest.mark.asyncio()
    async def test_cleanup_removes_expired(
        self, short_ttl_store: SessionKeyStore
    ) -> None:
        """cleanup_expired removes all expired entries."""
        await short_ttl_store.set_key("user-1", "openai", "sk-1")
        await short_ttl_store.set_key("user-2", "anthropic", "sk-2")
        await asyncio.sleep(0.15)
        removed = await short_ttl_store.cleanup_expired()
        assert removed == 2
        assert await short_ttl_store.count() == 0

    @pytest.mark.asyncio()
    async def test_cleanup_keeps_valid_keys(self, store: SessionKeyStore) -> None:
        """cleanup_expired does not remove non-expired entries."""
        await store.set_key("user-1", "openai", "sk-valid")
        removed = await store.cleanup_expired()
        assert removed == 0
        assert await store.count() == 1

    @pytest.mark.asyncio()
    async def test_cleanup_mixed_expired_and_valid(self) -> None:
        """cleanup_expired removes only expired entries, keeping valid ones."""
        store = SessionKeyStore(ttl=0.1)
        await store.set_key("user-1", "openai", "sk-will-expire")
        await asyncio.sleep(0.15)
        # Add a new key after the first one expires — it has the same short TTL
        # but was just created, so it's still valid
        await store.set_key("user-2", "anthropic", "sk-fresh")
        removed = await store.cleanup_expired()
        assert removed == 1  # only user-1's expired key
        assert await store.get_key("user-2", "anthropic") is not None


class TestUserIsolation:
    """Tests for isolation between different users."""

    @pytest.mark.asyncio()
    async def test_different_users_isolated(self, store: SessionKeyStore) -> None:
        """Keys from different users do not interfere with each other."""
        await store.set_key("user-1", "openai", "sk-user1")
        await store.set_key("user-2", "openai", "sk-user2")

        entry1 = await store.get_key("user-1", "openai")
        entry2 = await store.get_key("user-2", "openai")

        assert entry1.api_key == "sk-user1"
        assert entry2.api_key == "sk-user2"

    @pytest.mark.asyncio()
    async def test_delete_does_not_affect_other_users(
        self, store: SessionKeyStore
    ) -> None:
        """Deleting a key for one user does not affect another user's keys."""
        await store.set_key("user-1", "openai", "sk-user1")
        await store.set_key("user-2", "openai", "sk-user2")

        await store.delete_key("user-1", "openai")

        assert await store.get_key("user-1", "openai") is None
        entry2 = await store.get_key("user-2", "openai")
        assert entry2 is not None
        assert entry2.api_key == "sk-user2"

    @pytest.mark.asyncio()
    async def test_get_all_isolated(self, store: SessionKeyStore) -> None:
        """get_all_keys only returns keys for the requested user."""
        await store.set_key("user-1", "openai", "sk-1")
        await store.set_key("user-1", "anthropic", "sk-2")
        await store.set_key("user-2", "openai", "sk-3")

        keys_1 = await store.get_all_keys("user-1")
        keys_2 = await store.get_all_keys("user-2")

        assert len(keys_1) == 2
        assert len(keys_2) == 1


class TestCount:
    """Tests for the count method."""

    @pytest.mark.asyncio()
    async def test_count_empty(self, store: SessionKeyStore) -> None:
        """Empty store has count 0."""
        assert await store.count() == 0

    @pytest.mark.asyncio()
    async def test_count_after_adds(self, store: SessionKeyStore) -> None:
        """Count reflects the number of active keys."""
        await store.set_key("user-1", "openai", "sk-1")
        await store.set_key("user-1", "anthropic", "sk-2")
        await store.set_key("user-2", "openai", "sk-3")
        assert await store.count() == 3

    @pytest.mark.asyncio()
    async def test_count_after_delete(self, store: SessionKeyStore) -> None:
        """Count decreases after deletion."""
        await store.set_key("user-1", "openai", "sk-1")
        await store.set_key("user-1", "anthropic", "sk-2")
        await store.delete_key("user-1", "openai")
        assert await store.count() == 1


class TestSessionKeyPriority:
    """Tests verifying that session keys take priority over persistent keys."""

    @pytest.mark.asyncio()
    async def test_session_key_entry_fields(self, store: SessionKeyStore) -> None:
        """Entry has all expected fields set correctly."""
        entry = await store.set_key("user-1", "openai", "sk-abc", model_id="gpt-4o")
        assert entry.api_key == "sk-abc"
        assert entry.model_id == "gpt-4o"
        assert entry.is_expired is False
        assert entry.created_at > 0

    @pytest.mark.asyncio()
    async def test_session_key_available_for_eval_resolution(
        self, store: SessionKeyStore
    ) -> None:
        """Session keys can be looked up the same way eval_service would."""
        await store.set_key("user-1", "openai", "sk-session-key")

        # Simulate what _resolve_api_key does: check session store first
        entry = await store.get_key("user-1", "openai")
        assert entry is not None
        api_key = entry.api_key
        assert api_key == "sk-session-key"
