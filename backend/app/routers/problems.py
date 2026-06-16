"""Problem endpoints: browse the problem set and read a single problem.

Public reads:
    GET  /problems          -> list of problems (summary)
    GET  /problems/{slug}    -> full statement + sample test cases only

Authenticated write (admin-gated later, Phase 6):
    POST /problems           -> create a problem together with its test cases
"""

import re
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.repositories import problems, test_cases
from app.dependencies import get_current_user
from app.schemas.problem import (
    ProblemCreateRequest,
    ProblemDetailOut,
    ProblemSummaryOut,
)

router = APIRouter(prefix="/problems", tags=["problems"])


def _slugify(title: str) -> str:
    """Turn a title into a URL-friendly slug, e.g. 'Two Sum!' -> 'two-sum'."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "problem"


def _unique_slug(title: str) -> str:
    """Return a slug for ``title`` that is not already used, adding -2, -3, … if needed."""
    base = _slugify(title)
    slug = base
    suffix = 2
    while problems.slug_exists(slug):
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


@router.get("")
def list_problems():
    """Return all problems as lightweight summaries for the list page."""
    rows = problems.list_problems()
    return {"problems": [ProblemSummaryOut.from_row(row) for row in rows]}


@router.get("/{slug}")
def get_problem(slug: str):
    """Return one problem's full statement plus its sample test cases only."""
    problem = problems.get_problem_by_slug(slug)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    sample_rows = test_cases.list_sample_test_cases(problem["id"])
    return {"problem": ProblemDetailOut.from_row(problem, sample_rows)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_problem(
    request: ProblemCreateRequest,
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Create a new problem and its test cases (any logged-in user, for now)."""
    slug = _unique_slug(request.title)
    try:
        problem = problems.create_problem(
            title=request.title.strip(),
            slug=slug,
            statement=request.statement,
            input_format=request.input_format,
            output_format=request.output_format,
            constraints=request.constraints,
            difficulty=request.difficulty,
            time_limit_ms=request.time_limit_ms,
            memory_limit_mb=request.memory_limit_mb,
            created_by=current_user["id"],
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="A problem with this slug already exists.") from error

    for case in request.test_cases:
        test_cases.create_test_case(
            problem_id=problem["id"],
            input_text=case.input,
            expected_output=case.expected_output,
            is_sample=case.is_sample,
        )

    sample_rows = test_cases.list_sample_test_cases(problem["id"])
    return {"problem": ProblemDetailOut.from_row(problem, sample_rows)}
