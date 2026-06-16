"""Request/response models for the submissions endpoints."""

import sqlite3

from pydantic import BaseModel, Field


class SubmissionCreateRequest(BaseModel):
    """Body for ``POST /submissions``."""

    title: str = Field(min_length=1, max_length=120)
    language: str = "cpp"
    code: str = Field(min_length=1)
    output: str | None = None


class SubmissionUpdateRequest(BaseModel):
    """Body for ``PUT /submissions/{id}`` — every field is optional.

    Only the fields the client actually sends are applied; the router merges them
    with the existing row (see ``model_dump(exclude_unset=True)``).
    """

    title: str | None = Field(default=None, min_length=1, max_length=120)
    language: str | None = None
    code: str | None = Field(default=None, min_length=1)
    output: str | None = None


class SubmissionOut(BaseModel):
    """Shape of a submission returned to the client."""

    id: int
    title: str
    language: str
    code: str
    output: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "SubmissionOut":
        """Build a ``SubmissionOut`` from a database row (replaces ``serialize_submission``)."""
        return cls.model_validate(dict(row))
