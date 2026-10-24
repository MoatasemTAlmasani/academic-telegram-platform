"""Password hashing utilities."""

from __future__ import annotations

from pwdlib import PasswordHash


_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password using the recommended pwdlib algorithm."""
    if not password:
        raise ValueError("Password cannot be empty.")

    return _password_hash.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """Verify a password against its stored hash."""
    return _password_hash.verify(
        password,
        password_hash,
    )
