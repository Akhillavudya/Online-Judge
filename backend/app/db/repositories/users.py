"""All SQL for the ``users`` table.

Each function opens its own short-lived connection, runs one query, and returns
plain :class:`sqlite3.Row` objects (or ``None``). The caller decides what to do
with the result.
"""

import sqlite3

from app.core.time import now_iso
from app.db.database import get_connection


def create_user(name: str, email: str, password_hash: str) -> sqlite3.Row:
    """Insert a new user and return the freshly created row.

    Raises :class:`sqlite3.IntegrityError` when the email is already registered
    (the ``email`` column is UNIQUE); the router turns that into an HTTP 409.
    """
    created_at = now_iso()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, password_hash, created_at),
        )
        return connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()


def get_user_by_email(email: str) -> sqlite3.Row | None:
    """Look up a single user by email, or ``None`` if no match exists."""
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    """Look up a single user by primary key, or ``None`` if not found."""
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def set_user_role(user_id: int, role: str) -> sqlite3.Row | None:
    """Set a user's role (``'user'`` or ``'admin'``) and return the updated row.

    Returns ``None`` if no user has that id. Used by the ``make_admin.py`` script;
    there is deliberately no HTTP endpoint that lets a user promote themselves.
    """
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (role, user_id),
        )
        return connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
