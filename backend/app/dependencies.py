"""Shared FastAPI dependencies.

A dependency is a small function FastAPI runs *before* an endpoint to supply it
with something it needs. ``get_current_user`` is used by every protected route to
turn an ``Authorization: Bearer <token>`` header into the matching user row.
"""

import sqlite3
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.db.repositories import tokens


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> sqlite3.Row:
    """Resolve the logged-in user from the bearer token, or raise 401.

    Used as ``current_user: Annotated[sqlite3.Row, Depends(get_current_user)]`` in
    any endpoint that requires authentication.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
        )

    token = authorization.removeprefix("Bearer ").strip()
    user = tokens.get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )
    return user


def require_admin(
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
) -> sqlite3.Row:
    """Allow only admins through; otherwise raise 403.

    Layered on top of :func:`get_current_user`, so it first requires a valid
    login (401 if missing) and *then* checks the role (403 if not an admin). This
    is the difference between **authentication** (who you are) and
    **authorization** (what you're allowed to do): admin-only endpoints depend on
    this instead of ``get_current_user``.
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user
