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


def list_all_judge_submissions(user_id: int) -> list[sqlite3.Row]:
    """Return ALL of a user's judged attempts across every problem, newest first.

    Joins ``problems`` so each row carries the problem's title and slug, which the
    "My Submissions" page uses to label and link each attempt.
    """
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                js.id,
                js.language,
                js.verdict,
                js.passed_count,
                js.total_count,
                js.runtime_ms,
                js.created_at,
                p.title AS problem_title,
                p.slug AS problem_slug
            FROM judge_submissions AS js
            JOIN problems AS p ON p.id = js.problem_id
            WHERE js.user_id = ?
            ORDER BY js.id DESC
            """,
            (user_id,),
        ).fetchall()


def list_solved_problem_slugs(user_id: int) -> list[str]:
    """Return the slugs of every problem the user has an Accepted (AC) verdict on.

    A problem counts as *solved* the moment any one submission earns ``AC``.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT p.slug
            FROM judge_submissions AS js
            JOIN problems AS p ON p.id = js.problem_id
            WHERE js.user_id = ? AND js.verdict = 'AC'
            """,
            (user_id,),
        ).fetchall()
    return [row["slug"] for row in rows]
