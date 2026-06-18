"""Endpoints scoped to the *currently logged-in* user ("me").

These power the account-wide views — every problem the user has attempted and
which problems they've solved — as opposed to the per-problem history that lives
under ``/problems/{slug}/submissions``.

    GET /me/submissions  -> all judged attempts across every problem (newest first)
    GET /me/solved        -> slugs of problems the user has Accepted (AC)
"""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.db.repositories import judge_submissions
from app.dependencies import get_current_user
from app.schemas.judge import UserSubmissionOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/submissions")
def list_my_submissions(
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Return every judged attempt by the current user, across all problems."""
    rows = judge_submissions.list_all_judge_submissions(current_user["id"])
    return {"submissions": [UserSubmissionOut.from_row(row) for row in rows]}


@router.get("/solved")
def list_my_solved(
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Return the slugs of problems the current user has solved (got an AC on)."""
    slugs = judge_submissions.list_solved_problem_slugs(current_user["id"])
    return {"solved": slugs}
