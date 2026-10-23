"""
Password hashing and verification utilities.
Uses bcrypt directly for secure password storage.

Note: We use bcrypt directly (not via passlib) because passlib 1.7.4 has a
known compatibility issue with bcrypt >= 4.x (missing __about__ attribute).
Direct bcrypt usage is equally secure and removes the dependency on passlib's
bcrypt backend integration.
"""
import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password string to hash.

    Returns:
        A bcrypt-hashed string safe to store in the database.

    Raises:
        TypeError: If password is not a string.
        ValueError: If password is empty.
    """
    if not isinstance(password, str):
        raise TypeError(f"password must be a str, got {type(password).__name__}")
    if len(password) == 0:
        raise ValueError("password cannot be empty")
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Returns False (not raises) when the hash is invalid or doesn't match,
    so callers can handle authentication failures gracefully.

    Args:
        plaintext: The plaintext password to verify.
        hashed: The stored bcrypt hash to verify against.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    try:
        if not plaintext or not hashed:
            return False
        # bcrypt.checkpw requires bytes inputs
        plaintext_bytes = plaintext.encode("utf-8")
        hashed_bytes = hashed.encode("utf-8") if isinstance(hashed, str) else hashed
        return bcrypt.checkpw(plaintext_bytes, hashed_bytes)
    except Exception:
        # Handles malformed hashes (e.g., old plaintext stored in DB)
        return False
