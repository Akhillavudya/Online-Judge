"""Request/response models for submitting a solution to be judged."""

import sqlite3

from pydantic import BaseModel, Field


class SubmitRequest(BaseModel):
    """Body for ``POST /problems/{slug}/submit``."""

    language: str = "cpp"
    code: str = Field(min_length=1)


class JudgeSubmissionOut(BaseModel):
    """One judged attempt as shown in a user's submission history."""

    id: int
    language: str
    verdict: str
    passed_count: int
    total_count: int
    runtime_ms: int
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "JudgeSubmissionOut":
        return cls.model_validate(dict(row))


class JudgeResultOut(JudgeSubmissionOut):
    """The full result returned right after judging — adds a human-readable detail."""

    detail: str
