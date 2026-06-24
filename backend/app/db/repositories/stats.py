"""Aggregation SQL for profiles and the leaderboard (Phase 7).

The other repositories each map to a single table. This one is different: every
query here *summarises* data by joining ``judge_submissions`` with ``problems``
and ``users`` and rolling it up with ``GROUP BY`` / ``COUNT``. Keeping these
aggregation queries together makes the "stats" feature easy to find and reason
about, and keeps the row-level repos (``users.py``, ``judge_submissions.py``)
focused on plain CRUD.

Two ideas to keep straight:

* A problem is **solved** by a user the moment *any* of their submissions on it
  earns the ``AC`` verdict. So "solved" counts are always over **distinct**
  problem ids with an ``AC`` — never a raw row count (otherwise re-solving the
  same problem twice would count twice).
* A **submission** is one judged attempt (one ``judge_submissions`` row),
  regardless of verdict. "Total submissions" and "accepted submissions" are raw
  row counts.
"""

import sqlite3

from app.db.database import get_connection


def get_user_solved_by_difficulty(user_id: int) -> dict[str, int]:
    """Return how many *distinct* problems the user has solved, per difficulty.

    Example: ``{"easy": 4, "medium": 2, "hard": 0}``. Difficulties the user has
    not solved anything in are filled in as ``0`` so the caller always gets the
    full set of keys.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT p.difficulty AS difficulty,
                   COUNT(DISTINCT p.id) AS solved
            FROM judge_submissions AS js
            JOIN problems AS p ON p.id = js.problem_id
            WHERE js.user_id = ? AND js.verdict = 'AC'
            GROUP BY p.difficulty
            """,
            (user_id,),
        ).fetchall()

    breakdown = {"easy": 0, "medium": 0, "hard": 0}
    for row in rows:
        breakdown[row["difficulty"]] = row["solved"]
    return breakdown


def get_user_submission_stats(user_id: int) -> dict[str, int]:
    """Return raw submission counts for a user as a small dict.

    ``total_submissions`` = every judged attempt; ``accepted_submissions`` =
    attempts that earned ``AC``. ``total_solved`` = distinct problems solved
    (the headline number on a profile).
    """
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_submissions,
                SUM(CASE WHEN verdict = 'AC' THEN 1 ELSE 0 END) AS accepted_submissions,
                COUNT(DISTINCT CASE WHEN verdict = 'AC' THEN problem_id END) AS total_solved
            FROM judge_submissions
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    # SUM/COUNT over zero rows yields NULL/0; normalise to plain ints.
    return {
        "total_submissions": row["total_submissions"] or 0,
        "accepted_submissions": row["accepted_submissions"] or 0,
        "total_solved": row["total_solved"] or 0,
    }


def get_recent_submissions(user_id: int, limit: int = 10) -> list[sqlite3.Row]:
    """Return a user's most recent judged attempts (newest first), capped at ``limit``.

    Mirrors :func:`judge_submissions.list_all_judge_submissions` but limited — a
    profile only needs a short "recent activity" list, not the whole history.
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
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()


def get_leaderboard(limit: int = 50) -> list[sqlite3.Row]:
    """Return users ranked by number of problems solved, best first.

    A ``LEFT JOIN`` from ``users`` keeps everyone in the result even with no
    submissions, but the ``HAVING solved_count > 0`` filter then drops users who
    have not solved anything — a leaderboard of zeros is noise. Ties on solved
    count are broken by fewer total submissions (more efficient solver first),
    then by name for stability. The numeric rank is assigned by the caller.
    """
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                u.id AS user_id,
                u.name AS name,
                COUNT(DISTINCT CASE WHEN js.verdict = 'AC' THEN js.problem_id END) AS solved_count,
                COUNT(js.id) AS submission_count
            FROM users AS u
            LEFT JOIN judge_submissions AS js ON js.user_id = u.id
            GROUP BY u.id, u.name
            HAVING solved_count > 0
            ORDER BY solved_count DESC, submission_count ASC, u.name ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
