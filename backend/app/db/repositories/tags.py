"""All SQL for tags (the ``tags`` and ``problem_tags`` tables).

A *tag* is a short label like ``array`` or ``math``. Tags are stored once in
``tags`` and linked to problems through the ``problem_tags`` join table, so one
tag can belong to many problems and one problem can have many tags (a classic
many-to-many relationship).
"""

import sqlite3

from app.db.database import get_connection


def list_tag_names() -> list[str]:
    """Return every tag name in alphabetical order (for the filter dropdown)."""
    with get_connection() as connection:
        rows = connection.execute("SELECT name FROM tags ORDER BY name").fetchall()
    return [row["name"] for row in rows]


def get_tags_for_problem(problem_id: int) -> list[str]:
    """Return the tag names attached to one problem, alphabetically."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT t.name
            FROM problem_tags AS pt
            JOIN tags AS t ON t.id = pt.tag_id
            WHERE pt.problem_id = ?
            ORDER BY t.name
            """,
            (problem_id,),
        ).fetchall()
    return [row["name"] for row in rows]


def get_tags_by_problem_ids(problem_ids: list[int]) -> dict[int, list[str]]:
    """Return ``{problem_id: [tag, ...]}`` for several problems in one query.

    Used by the problem-list view to attach tags to every row without firing a
    separate query per problem (avoids the classic N+1 problem).
    """
    if not problem_ids:
        return {}

    placeholders = ",".join("?" for _ in problem_ids)
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT pt.problem_id AS problem_id, t.name AS name
            FROM problem_tags AS pt
            JOIN tags AS t ON t.id = pt.tag_id
            WHERE pt.problem_id IN ({placeholders})
            ORDER BY t.name
            """,
            problem_ids,
        ).fetchall()

    result: dict[int, list[str]] = {pid: [] for pid in problem_ids}
    for row in rows:
        result[row["problem_id"]].append(row["name"])
    return result


def set_problem_tags(problem_id: int, names: list[str]) -> None:
    """Replace a problem's tags with ``names`` (creating any tag that's new).

    Tag names are lower-cased and de-duplicated so ``Array`` and ``array`` map to
    the same tag. Empty names are ignored.
    """
    cleaned = []
    seen = set()
    for raw in names:
        name = raw.strip().lower()
        if name and name not in seen:
            seen.add(name)
            cleaned.append(name)

    with get_connection() as connection:
        # Start from a clean slate so re-seeding/editing is idempotent.
        connection.execute(
            "DELETE FROM problem_tags WHERE problem_id = ?", (problem_id,)
        )
        for name in cleaned:
            connection.execute(
                "INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,)
            )
            tag_id = connection.execute(
                "SELECT id FROM tags WHERE name = ?", (name,)
            ).fetchone()["id"]
            connection.execute(
                "INSERT OR IGNORE INTO problem_tags (problem_id, tag_id) VALUES (?, ?)",
                (problem_id, tag_id),
            )
