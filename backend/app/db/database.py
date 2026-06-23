"""SQLite connection helper and schema setup.

This module is the only place that knows *how* to open the database. Everything
else asks for a connection via :func:`get_connection`, and the table layout is
created once at startup by :func:`init_database`.
"""

import sqlite3

from app.config import settings


def get_connection() -> sqlite3.Connection:
    """Open a new SQLite connection with row access by column name.

    Setting ``row_factory`` to :class:`sqlite3.Row` lets callers read columns like
    ``row["email"]`` instead of by numeric index, which keeps the repositories
    readable.
    """
    connection = sqlite3.connect(settings.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    """Return ``True`` if ``table`` already has a column named ``column``.

    Used by the lightweight migrations below. ``PRAGMA table_info`` lists one row
    per column; row[1] is the column name.
    """
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def init_database() -> None:
    """Create the tables if they do not exist yet, then run small migrations.

    Safe to run on every startup: ``CREATE TABLE IF NOT EXISTS`` is a no-op when
    the tables are already present, so existing data in ``compiler.db`` is kept.
    Migrations that add columns to *existing* tables (e.g. ``users.role``) are
    applied separately with ``ALTER TABLE`` — see :func:`_run_migrations`.
    """
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_tokens (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                output TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                statement TEXT NOT NULL,
                input_format TEXT,
                output_format TEXT,
                constraints TEXT,
                difficulty TEXT NOT NULL DEFAULT 'easy',
                time_limit_ms INTEGER NOT NULL DEFAULT 2000,
                memory_limit_mb INTEGER NOT NULL DEFAULT 256,
                created_by INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id INTEGER NOT NULL,
                input TEXT NOT NULL,
                expected_output TEXT NOT NULL,
                is_sample INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS problem_tags (
                problem_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (problem_id, tag_id),
                FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS judge_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                problem_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                verdict TEXT NOT NULL,
                passed_count INTEGER NOT NULL DEFAULT 0,
                total_count INTEGER NOT NULL DEFAULT 0,
                runtime_ms INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE CASCADE
            )
            """
        )

        _run_migrations(connection)


def _run_migrations(connection: sqlite3.Connection) -> None:
    """Apply schema changes to tables that already exist in older databases.

    ``CREATE TABLE IF NOT EXISTS`` only helps for brand-new tables; it never adds
    a column to a table that is already there. So when we introduce a new column
    on an existing table we add it here with ``ALTER TABLE``, guarded by a column
    check so it runs at most once. Each migration is small and idempotent.
    """
    # Phase 6: user roles. Existing accounts default to the regular 'user' role.
    if not _column_exists(connection, "users", "role"):
        connection.execute(
            "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'"
        )
