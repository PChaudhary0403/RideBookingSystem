"""
Unit tests for password hashing utility.
RED PHASE: These tests must fail before the implementation is added.
"""
import pytest


class TestPasswordHashing:
    """Tests for the password hashing utility (Bug #1 fix)."""

    def test_hash_password_returns_string(self):
        from utils.security import hash_password
        hashed = hash_password("mysecretpassword")
        assert isinstance(hashed, str)

    def test_hash_password_is_not_plaintext(self):
        from utils.security import hash_password
        plaintext = "mysecretpassword"
        hashed = hash_password(plaintext)
        assert hashed != plaintext

    def test_hash_password_produces_bcrypt_hash(self):
        from utils.security import hash_password
        hashed = hash_password("mysecretpassword")
        # bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        from utils.security import hash_password, verify_password
        plaintext = "mysecretpassword"
        hashed = hash_password(plaintext)
        assert verify_password(plaintext, hashed) is True

    def test_verify_password_incorrect(self):
        from utils.security import hash_password, verify_password
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty_string_fails(self):
        from utils.security import hash_password, verify_password
        hashed = hash_password("correctpassword")
        assert verify_password("", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses random salts — same input → different hashes."""
        from utils.security import hash_password
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2

    def test_verify_password_with_hash_from_different_run(self):
        """Verification must work across hash instances (salt is embedded)."""
        from utils.security import hash_password, verify_password
        hashed = hash_password("somepassword")
        # Simulate re-loading the hash from DB
        assert verify_password("somepassword", hashed) is True

    def test_hash_password_raises_on_none(self):
        from utils.security import hash_password
        with pytest.raises((TypeError, ValueError)):
            hash_password(None)
