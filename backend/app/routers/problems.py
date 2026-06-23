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

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.repositories import judge_submissions, problems, tags, test_cases
from app.dependencies import get_current_user
from app.schemas.judge import JudgeResultOut, JudgeSubmissionOut, SubmitRequest
from app.schemas.problem import (
    Difficulty,
    ProblemCreateRequest,
    ProblemDetailOut,
    ProblemListOut,
    ProblemSummaryOut,
)
from app.services.judge import judge_submission
from app.services.languages import SUPPORTED_LANGUAGES

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


@router.get("", response_model=ProblemListOut)
def list_problems(
    search: Annotated[str | None, Query(max_length=200)] = None,
    difficulty: Difficulty | None = None,
    tag: Annotated[str | None, Query(max_length=50)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Return a filtered, paginated page of problems for the list page.

    Query params (all optional): ``search`` (title contains), ``difficulty``,
    ``tag``, ``page`` (1-based), ``limit`` (per page). Returns the page of
    problems plus the ``total`` count so the frontend can render a pager.
    """
    offset = (page - 1) * limit
    rows = problems.list_problems(
        search=search, difficulty=difficulty, tag=tag, limit=limit, offset=offset
    )
    total = problems.count_problems(search=search, difficulty=difficulty, tag=tag)

    # Attach each problem's tags in a single follow-up query (no N+1).
    tags_by_id = tags.get_tags_by_problem_ids([row["id"] for row in rows])
    return {
        "problems": [
            ProblemSummaryOut.from_row(row, tags_by_id.get(row["id"], []))
            for row in rows
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/tags")
def list_tags():
    """Return all tag names (for the discovery filter dropdown)."""
    return {"tags": tags.list_tag_names()}


@router.get("/{slug}")
def get_problem(slug: str):
    """Return one problem's full statement plus its sample test cases only."""
    problem = problems.get_problem_by_slug(slug)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    sample_rows = test_cases.list_sample_test_cases(problem["id"])
    problem_tags = tags.get_tags_for_problem(problem["id"])
    return {"problem": ProblemDetailOut.from_row(problem, sample_rows, problem_tags)}


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

    if request.language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise HTTPException(
            status_code=400, detail=f"Unsupported language. Supported: {supported}."
        )

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

    if request.tags:
        tags.set_problem_tags(problem["id"], request.tags)

    sample_rows = test_cases.list_sample_test_cases(problem["id"])
    problem_tags = tags.get_tags_for_problem(problem["id"])
    return {"problem": ProblemDetailOut.from_row(problem, sample_rows, problem_tags)}
