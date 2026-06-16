"""All SQL for the ``problems`` table (the questions users solve)."""

import sqlite3

from app.core.time import now_iso
from app.db.database import get_connection


def create_problem(
    title: str,
    slug: str,
    statement: str,
    input_format: str | None,
    output_format: str | None,
    constraints: str | None,
    difficulty: str,
    time_limit_ms: int,
    memory_limit_mb: int,
    created_by: int | None,
) -> sqlite3.Row:
    """Insert a new problem and return the created row.

    Raises :class:`sqlite3.IntegrityError` if the slug is already taken (the
    ``slug`` column is UNIQUE); the router turns that into an HTTP 409.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO problems (
                title, slug, statement, input_format, output_format,
                constraints, difficulty, time_limit_ms, memory_limit_mb,
                created_by, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                slug,
                statement,
                input_format,
                output_format,
                constraints,
                difficulty,
                time_limit_ms,
                memory_limit_mb,
                created_by,
                now_iso(),
            ),
        )
        return connection.execute(
            "SELECT * FROM problems WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()


def list_problems() -> list[sqlite3.Row]:
    """Return all problems, newest first (lightweight columns for the list view)."""
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, title, slug, difficulty, created_at
            FROM problems
            ORDER BY id DESC
            """
        ).fetchall()


def get_problem_by_slug(slug: str) -> sqlite3.Row | None:
    """Return one full problem by its slug, or ``None`` if it does not exist."""
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM problems WHERE slug = ?",
            (slug,),
        ).fetchone()


def slug_exists(slug: str) -> bool:
    """Return ``True`` if a problem with this slug already exists."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM problems WHERE slug = ?",
            (slug,),
        ).fetchone()
    return row is not None
