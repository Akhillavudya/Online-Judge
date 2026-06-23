"""Request/response models for the authentication endpoints."""

import sqlite3

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Body for ``POST /auth/register``."""

    name: str = Field(min_length=2, max_length=80)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    """Body for ``POST /auth/login``."""

    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str


class UserOut(BaseModel):
    """Public view of a user (never includes the password hash)."""

    id: int
    name: str
    email: str
    role: str = "user"
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "UserOut":
        """Build a ``UserOut`` from a database row.

        ``sqlite3.Row`` supports ``dict(row)``, which gives us a plain mapping
        Pydantic can validate. This replaces the old ``serialize_user`` helper.
        """
        return cls.model_validate(dict(row))
