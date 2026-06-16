"""All SQL for the ``auth_tokens`` table (the bearer tokens used for login)."""

import sqlite3

from app.core.time import now_iso
from app.db.database import get_connection


def insert_token(token: str, user_id: int) -> None:
    """Store a freshly issued token for the given user."""
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO auth_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, now_iso()),
        )


def get_user_by_token(token: str) -> sqlite3.Row | None:
    """Return the user that owns ``token`` by joining tokens to users.

    Selects only the public user columns; returns ``None`` for an unknown token.
    """
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT users.id, users.name, users.email, users.created_at
            FROM auth_tokens
            JOIN users ON users.id = auth_tokens.user_id
            WHERE auth_tokens.token = ?
            """,
            (token,),
        ).fetchone()


def delete_token(token: str) -> None:
    """Remove a token so it can no longer be used (logout)."""
    with get_connection() as connection:
        connection.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
