"""All SQL for the ``test_cases`` table.

A test case is one ``input`` paired with its ``expected_output``. ``is_sample``
marks the cases that are safe to show the user on the problem page; the rest stay
hidden and will be used by the judge (Phase 2).
"""

import sqlite3

from app.db.database import get_connection


def create_test_case(
    problem_id: int,
    input_text: str,
    expected_output: str,
    is_sample: bool,
) -> None:
    """Insert one test case for a problem."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO test_cases (problem_id, input, expected_output, is_sample)
            VALUES (?, ?, ?, ?)
            """,
            (problem_id, input_text, expected_output, 1 if is_sample else 0),
        )


def list_sample_test_cases(problem_id: int) -> list[sqlite3.Row]:
    """Return only the *sample* test cases for a problem (safe to show the user)."""
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, input, expected_output
            FROM test_cases
            WHERE problem_id = ? AND is_sample = 1
            ORDER BY id
            """,
            (problem_id,),
        ).fetchall()


def list_all_test_cases(problem_id: int) -> list[sqlite3.Row]:
    """Return every test case (sample + hidden) for a problem.

    Used by the judge in Phase 2 — never exposed directly through a public route.
    The admin endpoints (Phase 6) also use it so an admin can review hidden cases.
    """
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, input, expected_output, is_sample
            FROM test_cases
            WHERE problem_id = ?
            ORDER BY id
            """,
            (problem_id,),
        ).fetchall()


def get_test_case(test_case_id: int) -> sqlite3.Row | None:
    """Return one test case by id, or ``None`` if it does not exist."""
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM test_cases WHERE id = ?",
            (test_case_id,),
        ).fetchone()


def delete_test_case(test_case_id: int) -> int:
    """Delete one test case by id and return how many rows were removed (0 or 1)."""
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM test_cases WHERE id = ?",
            (test_case_id,),
        )
        return cursor.rowcount
