"""CRUD endpoints for a user's saved submissions (all require authentication)."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.repositories import submissions
from app.dependencies import get_current_user
from app.schemas.submission import (
    SubmissionCreateRequest,
    SubmissionOut,
    SubmissionUpdateRequest,
)
from app.services.languages import SUPPORTED_LANGUAGES

router = APIRouter(prefix="/submissions", tags=["submissions"])


def _reject_unsupported(language: str) -> None:
    """Raise a 400 if ``language`` is not one the judge/executor supports."""
    if language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise HTTPException(
            status_code=400, detail=f"Unsupported language. Supported: {supported}."
        )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_submission(
    request: SubmissionCreateRequest,
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Save a new submission for the current user."""
    _reject_unsupported(request.language)

    submission = submissions.create_submission(
        user_id=current_user["id"],
        title=request.title.strip(),
        language=request.language,
        code=request.code,
        output=request.output,
    )
    return {"submission": SubmissionOut.from_row(submission)}


@router.get("")
def list_submissions(current_user: Annotated[sqlite3.Row, Depends(get_current_user)]):
    """List the current user's submissions, newest first."""
    rows = submissions.list_submissions(current_user["id"])
    return {"submissions": [SubmissionOut.from_row(row) for row in rows]}


@router.get("/{submission_id}")
def get_submission(
    submission_id: int,
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Fetch a single submission owned by the current user."""
    submission = submissions.get_submission(submission_id, current_user["id"])
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return {"submission": SubmissionOut.from_row(submission)}


@router.put("/{submission_id}")
def update_submission(
    submission_id: int,
    request: SubmissionUpdateRequest,
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Apply a partial update to a submission and return the updated record."""
    # Keep only the fields the client actually sent.
    updates = request.model_dump(exclude_unset=True)
    if "language" in updates:
        _reject_unsupported(updates["language"])
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    existing = submissions.get_submission(submission_id, current_user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="Submission not found.")

    # Merge the requested changes onto the existing values before saving.
    title = updates.get("title", existing["title"]).strip()
    submission = submissions.update_submission(
        submission_id=submission_id,
        user_id=current_user["id"],
        title=title,
        language=updates.get("language", existing["language"]),
        code=updates.get("code", existing["code"]),
        output=updates.get("output", existing["output"]),
    )
    return {"submission": SubmissionOut.from_row(submission)}


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    submission_id: int,
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Delete a submission owned by the current user."""
    deleted = submissions.delete_submission(submission_id, current_user["id"])
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Submission not found.")
