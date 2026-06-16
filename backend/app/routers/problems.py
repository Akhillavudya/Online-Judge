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

from app.db.repositories import judge_submissions, problems, test_cases
from app.dependencies import get_current_user
from app.schemas.judge import JudgeResultOut, JudgeSubmissionOut, SubmitRequest
from app.schemas.problem import (
    ProblemCreateRequest,
    ProblemDetailOut,
    ProblemSummaryOut,
)
from app.services.judge import SUPPORTED_LANGUAGE, judge_submission

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


@router.post("/{slug}/submit")
def submit_solution(
    slug: str,
    request: SubmitRequest,
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Judge a submission against ALL of a problem's test cases and store the result."""
    problem = problems.get_problem_by_slug(slug)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    if request.language != SUPPORTED_LANGUAGE:
        raise HTTPException(status_code=400, detail="Only C++ is supported right now.")

    cases = test_cases.list_all_test_cases(problem["id"])
    if not cases:
        raise HTTPException(status_code=400, detail="This problem has no test cases yet.")

    report = judge_submission(
        language=request.language,
        code=request.code,
        test_cases=cases,
        time_limit_ms=problem["time_limit_ms"],
    )

    saved = judge_submissions.create_judge_submission(
        user_id=current_user["id"],
        problem_id=problem["id"],
        language=request.language,
        code=request.code,
        verdict=report["verdict"],
        passed_count=report["passed_count"],
        total_count=report["total_count"],
        runtime_ms=report["runtime_ms"],
    )

    return {
        "result": JudgeResultOut(
            id=saved["id"],
            language=saved["language"],
            verdict=saved["verdict"],
            passed_count=saved["passed_count"],
            total_count=saved["total_count"],
            runtime_ms=saved["runtime_ms"],
            created_at=saved["created_at"],
            detail=report["detail"],
        )
    }


@router.get("/{slug}/submissions")
def list_problem_submissions(
    slug: str,
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Return the current user's previous attempts at this problem (newest first)."""
    problem = problems.get_problem_by_slug(slug)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    rows = judge_submissions.list_judge_submissions(current_user["id"], problem["id"])
    return {"submissions": [JudgeSubmissionOut.from_row(row) for row in rows]}


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
