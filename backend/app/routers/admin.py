"""Admin-only endpoints for managing problems and their test cases (Phase 6).

Every route here depends on :func:`require_admin`, so a regular logged-in user
gets a 403. This is the *authorization* layer on top of the *authentication* that
``get_current_user`` already provides. Problem creation used to live on the public
``POST /problems`` route; Phase 6 moves it here and locks it down.

Routes (all require an admin token):
    POST   /admin/problems                       -> create a problem + its test cases
    PUT    /admin/problems/{slug}                 -> edit a problem's fields + tags
    GET    /admin/problems/{slug}                 -> full problem incl. hidden test cases
    POST   /admin/problems/{slug}/test-cases      -> add one test case
    DELETE /admin/test-cases/{test_case_id}       -> remove one test case
"""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.repositories import problems, tags, test_cases
from app.dependencies import require_admin
from app.routers.problems import _unique_slug
from app.schemas.problem import (
    AdminProblemDetailOut,
    ProblemCreateRequest,
    ProblemDetailOut,
    ProblemUpdateRequest,
    TestCaseCreateRequest,
    TestCaseFullOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])

# Reused by every route here: 401 if not logged in, 403 if not an admin.
AdminUser = Annotated[sqlite3.Row, Depends(require_admin)]


def _get_problem_or_404(slug: str) -> sqlite3.Row:
    """Fetch a problem by slug or raise 404 (shared by the admin routes)."""
    problem = problems.get_problem_by_slug(slug)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")
    return problem


@router.post("/problems", status_code=status.HTTP_201_CREATED)
def create_problem(request: ProblemCreateRequest, _admin: AdminUser):
    """Create a new problem together with its test cases and tags."""
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
            created_by=_admin["id"],
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409, detail="A problem with this slug already exists."
        ) from error

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


@router.put("/problems/{slug}")
def update_problem(slug: str, request: ProblemUpdateRequest, _admin: AdminUser):
    """Edit an existing problem's fields and tags (the slug stays fixed)."""
    problem = _get_problem_or_404(slug)
    updated = problems.update_problem(
        problem_id=problem["id"],
        title=request.title.strip(),
        statement=request.statement,
        input_format=request.input_format,
        output_format=request.output_format,
        constraints=request.constraints,
        difficulty=request.difficulty,
        time_limit_ms=request.time_limit_ms,
        memory_limit_mb=request.memory_limit_mb,
    )
    tags.set_problem_tags(problem["id"], request.tags)

    sample_rows = test_cases.list_sample_test_cases(problem["id"])
    problem_tags = tags.get_tags_for_problem(problem["id"])
    return {"problem": ProblemDetailOut.from_row(updated, sample_rows, problem_tags)}


@router.get("/problems/{slug}")
def get_problem_for_admin(slug: str, _admin: AdminUser):
    """Return a problem with *all* its test cases (including hidden ones)."""
    problem = _get_problem_or_404(slug)
    case_rows = test_cases.list_all_test_cases(problem["id"])
    problem_tags = tags.get_tags_for_problem(problem["id"])
    return {"problem": AdminProblemDetailOut.from_row(problem, case_rows, problem_tags)}


@router.post("/problems/{slug}/test-cases", status_code=status.HTTP_201_CREATED)
def add_test_case(slug: str, request: TestCaseCreateRequest, _admin: AdminUser):
    """Add a single test case (sample or hidden) to an existing problem."""
    problem = _get_problem_or_404(slug)
    test_cases.create_test_case(
        problem_id=problem["id"],
        input_text=request.input,
        expected_output=request.expected_output,
        is_sample=request.is_sample,
    )
    case_rows = test_cases.list_all_test_cases(problem["id"])
    return {"test_cases": [TestCaseFullOut.from_row(r) for r in case_rows]}


@router.delete("/test-cases/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(test_case_id: int, _admin: AdminUser):
    """Remove one test case by id."""
    deleted = test_cases.delete_test_case(test_case_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Test case not found.")
