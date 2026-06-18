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


def _build_filters(
    search: str | None,
    difficulty: str | None,
    tag: str | None,
) -> tuple[str, str, list]:
    """Build the shared JOIN/WHERE clause (and params) for listing + counting.

    Returns ``(join_sql, where_sql, params)`` so :func:`list_problems` and
    :func:`count_problems` apply *exactly the same* filters — the count must match
    the rows being paginated.
    """
    join_sql = ""
    wheres: list[str] = []
    params: list = []

    if tag:
        # Only join the tag tables when actually filtering by tag.
        join_sql = (
            " JOIN problem_tags AS pt ON pt.problem_id = p.id"
            " JOIN tags AS t ON t.id = pt.tag_id"
        )
        wheres.append("t.name = ?")
        params.append(tag.strip().lower())
    if difficulty:
        wheres.append("p.difficulty = ?")
        params.append(difficulty)
    if search:
        wheres.append("p.title LIKE ?")
        params.append(f"%{search}%")

    where_sql = (" WHERE " + " AND ".join(wheres)) if wheres else ""
    return join_sql, where_sql, params


def list_problems(
    search: str | None = None,
    difficulty: str | None = None,
    tag: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[sqlite3.Row]:
    """Return a page of problems matching the filters, newest first.

    ``limit``/``offset`` implement pagination; ``search`` matches the title,
    ``difficulty`` and ``tag`` narrow the set. All filters are optional.
    """
    join_sql, where_sql, params = _build_filters(search, difficulty, tag)
    with get_connection() as connection:
        return connection.execute(
            f"""
            SELECT p.id, p.title, p.slug, p.difficulty, p.created_at
            FROM problems AS p{join_sql}{where_sql}
            ORDER BY p.id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()


def count_problems(
    search: str | None = None,
    difficulty: str | None = None,
    tag: str | None = None,
) -> int:
    """Return how many problems match the filters (for the pagination total)."""
    join_sql, where_sql, params = _build_filters(search, difficulty, tag)
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT COUNT(*) AS n FROM problems AS p{join_sql}{where_sql}",
            params,
        ).fetchone()
    return row["n"]


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
