"""Request/response models for the problems endpoints."""

import sqlite3
from typing import Literal

from pydantic import BaseModel, Field

# The three difficulty levels, validated automatically by Pydantic.
Difficulty = Literal["easy", "medium", "hard"]


class TestCaseIn(BaseModel):
    """One test case supplied when creating a problem."""

    input: str = ""
    expected_output: str
    is_sample: bool = False


class ProblemCreateRequest(BaseModel):
    """Body for ``POST /problems`` (creating a problem with its test cases).

    For now any logged-in user may create a problem; this will be restricted to
    admins in Phase 6.
    """

    title: str = Field(min_length=2, max_length=200)
    statement: str = Field(min_length=1)
    input_format: str | None = None
    output_format: str | None = None
    constraints: str | None = None
    difficulty: Difficulty = "easy"
    time_limit_ms: int = Field(default=2000, ge=100, le=15000)
    memory_limit_mb: int = Field(default=256, ge=16, le=1024)
    tags: list[str] = Field(default_factory=list)
    test_cases: list[TestCaseIn] = Field(default_factory=list)


class ProblemUpdateRequest(BaseModel):
    """Body for ``PUT /admin/problems/{slug}`` (edit a problem's fields).

    The slug is not editable so existing links keep working. Test cases are
    managed through their own admin endpoints, not here.
    """

    title: str = Field(min_length=2, max_length=200)
    statement: str = Field(min_length=1)
    input_format: str | None = None
    output_format: str | None = None
    constraints: str | None = None
    difficulty: Difficulty = "easy"
    time_limit_ms: int = Field(default=2000, ge=100, le=15000)
    memory_limit_mb: int = Field(default=256, ge=16, le=1024)
    tags: list[str] = Field(default_factory=list)


class TestCaseCreateRequest(TestCaseIn):
    """Body for ``POST /admin/problems/{slug}/test-cases`` (add one test case)."""


class TestCaseSampleOut(BaseModel):
    """A sample test case shown to the user on the problem page."""

    id: int
    input: str
    expected_output: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "TestCaseSampleOut":
        return cls.model_validate(dict(row))


class TestCaseFullOut(BaseModel):
    """A full test case (incl. hidden ones) — only ever returned to admins."""

    id: int
    input: str
    expected_output: str
    is_sample: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "TestCaseFullOut":
        return cls.model_validate(dict(row))


class ProblemSummaryOut(BaseModel):
    """Lightweight problem info for the problem-list view."""

    id: int
    title: str
    slug: str
    difficulty: str
    created_at: str
    tags: list[str] = []

    @classmethod
    def from_row(cls, row: sqlite3.Row, tags: list[str] | None = None) -> "ProblemSummaryOut":
        data = dict(row)
        data["tags"] = tags or []
        return cls.model_validate(data)


class ProblemListOut(BaseModel):
    """A paginated page of problems plus the total count for the pager."""

    problems: list[ProblemSummaryOut]
    total: int
    page: int
    limit: int


class ProblemDetailOut(BaseModel):
    """Full problem statement plus only its sample test cases."""

    id: int
    title: str
    slug: str
    statement: str
    input_format: str | None
    output_format: str | None
    constraints: str | None
    difficulty: str
    time_limit_ms: int
    memory_limit_mb: int
    created_at: str
    tags: list[str] = []
    sample_test_cases: list[TestCaseSampleOut]

    @classmethod
    def from_row(
        cls,
        row: sqlite3.Row,
        sample_rows: list[sqlite3.Row],
        tags: list[str] | None = None,
    ) -> "ProblemDetailOut":
        """Build the detail view from a problem row + its sample test-case rows."""
        data = dict(row)
        data["tags"] = tags or []
        data["sample_test_cases"] = [TestCaseSampleOut.from_row(r) for r in sample_rows]
        return cls.model_validate(data)


class AdminProblemDetailOut(BaseModel):
    """Admin view of a problem: full statement plus *all* test cases (incl. hidden)."""

    id: int
    title: str
    slug: str
    statement: str
    input_format: str | None
    output_format: str | None
    constraints: str | None
    difficulty: str
    time_limit_ms: int
    memory_limit_mb: int
    created_at: str
    tags: list[str] = []
    test_cases: list[TestCaseFullOut]

    @classmethod
    def from_row(
        cls,
        row: sqlite3.Row,
        case_rows: list[sqlite3.Row],
        tags: list[str] | None = None,
    ) -> "AdminProblemDetailOut":
        data = dict(row)
        data["tags"] = tags or []
        data["test_cases"] = [TestCaseFullOut.from_row(r) for r in case_rows]
        return cls.model_validate(data)
