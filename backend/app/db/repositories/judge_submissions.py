"""All SQL for the ``judge_submissions`` table.

A *judge submission* is one attempt at a problem: the code a user submitted plus
the verdict the judge gave it (Accepted / Wrong Answer / …). This is separate from
the ``submissions`` table, which stores free-form saved code snippets.
"""

import sqlite3

from app.core.time import now_iso
from app.db.database import get_connection


def create_judge_submission(
    user_id: int,
    problem_id: int,
    language: str,
    code: str,
    verdict: str,
    passed_count: int,
    total_count: int,
    runtime_ms: int,
) -> sqlite3.Row:
    """Record one judged attempt and return the created row."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO judge_submissions (
                user_id, problem_id, language, code, verdict,
                passed_count, total_count, runtime_ms, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                problem_id,
                language,
                code,
                verdict,
                passed_count,
                total_count,
                runtime_ms,
                now_iso(),
            ),
        )
        return connection.execute(
            "SELECT * FROM judge_submissions WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()


def list_judge_submissions(user_id: int, problem_id: int) -> list[sqlite3.Row]:
    """Return a user's attempts at one problem, newest first."""
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, language, verdict, passed_count, total_count, runtime_ms, created_at
            FROM judge_submissions
            WHERE user_id = ? AND problem_id = ?
            ORDER BY id DESC
            """,
            (user_id, problem_id),
        ).fetchall()
