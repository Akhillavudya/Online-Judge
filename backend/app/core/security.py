"""Security primitives: password hashing and auth-token generation.

These functions deal only with cryptography and have no knowledge of the
database or of HTTP requests, which keeps them easy to test and reuse.
"""

import base64
import hashlib
import hmac
import secrets

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password for safe storage.

    Returns a self-describing string in the form
    ``pbkdf2_sha256$<iterations>$<salt>$<digest>`` so :func:`verify_password`
    can re-derive the hash later without any extra stored metadata.
    """
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        settings.PASSWORD_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${settings.PASSWORD_ITERATIONS}$"
        f"{base64.b64encode(salt).decode()}$"
        f"{base64.b64encode(digest).decode()}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Return ``True`` when ``password`` matches the stored ``password_hash``.

    Uses :func:`hmac.compare_digest` for a constant-time comparison so attackers
    cannot learn the hash by measuring how long the check takes.
    """
    try:
        algorithm, iterations, salt, expected_digest = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.b64decode(salt),
            int(iterations),
        )
        return hmac.compare_digest(
            base64.b64encode(digest).decode(),
            expected_digest,
        )
    except (ValueError, TypeError):
        return False


def generate_token_value() -> str:
    """Create a new, URL-safe random session token."""
    return secrets.token_urlsafe(settings.TOKEN_BYTES)
