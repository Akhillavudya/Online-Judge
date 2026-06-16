"""All SQL for the ``submissions`` table (a user's saved code snippets).

Every query is scoped by ``user_id`` so a user can only ever touch their own
submissions, even when they pass an id that belongs to someone else.
"""

import sqlite3

from app.core.time import now_iso
from app.db.database import get_connection


def create_submission(
    user_id: int,
    title: str,
    language: str,
    code: str,
    output: str | None,
) -> sqlite3.Row:
    """Insert a new submission and return the created row."""
    timestamp = now_iso()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO submissions
                (user_id, title, language, code, output, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, language, code, output, timestamp, timestamp),
        )
        return connection.execute(
            "SELECT * FROM submissions WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()


def list_submissions(user_id: int) -> list[sqlite3.Row]:
    """Return all of a user's submissions, newest update first."""
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT * FROM submissions
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()


def get_submission(submission_id: int, user_id: int) -> sqlite3.Row | None:
    """Return one submission owned by the user, or ``None`` if it does not exist."""
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM submissions WHERE id = ? AND user_id = ?",
            (submission_id, user_id),
        ).fetchone()


def update_submission(
    submission_id: int,
    user_id: int,
    title: str,
    language: str,
    code: str,
    output: str | None,
) -> sqlite3.Row:
    """Overwrite a submission's fields and bump ``updated_at``.

    The router is responsible for merging partial updates with the existing row
    before calling this, so the four values passed here are always the final
    desired state.
    """
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE submissions
            SET title = ?, language = ?, code = ?, output = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (title, language, code, output, now_iso(), submission_id, user_id),
        )
        return connection.execute(
            "SELECT * FROM submissions WHERE id = ?",
            (submission_id,),
        ).fetchone()


def delete_submission(submission_id: int, user_id: int) -> int:
    """Delete a submission and return how many rows were removed (0 or 1)."""
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM submissions WHERE id = ? AND user_id = ?",
            (submission_id, user_id),
        )
        return cursor.rowcount
