"""Top-level package for the Online Judge backend.

The application is organised into clear layers so new contributors always know
where a piece of code belongs:

    routers/      -> HTTP layer only: read the request, call a service/repo, return.
    services/     -> business logic (compile & run C++, call the AI reviewer).
    db/           -> database connection plus the repositories that hold all SQL.
    schemas/      -> Pydantic request/response models.
    core/         -> low-level helpers shared everywhere (password hashing, tokens).
    config.py     -> the single source of environment variables and file paths.

Golden rule: routers never write SQL, and SQL never lives outside db/repositories.
"""
