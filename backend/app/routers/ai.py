"""The AI code-review endpoint (requires authentication)."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.ai import AIReviewRequest
from app.schemas.auth import UserOut
from app.services.ai_review import AIReviewError, review_code
from app.services.languages import SUPPORTED_LANGUAGES

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/review")
def ai_review(
    request: AIReviewRequest,
    current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Return an AI-generated review of the submitted code."""
    if request.language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise HTTPException(
            status_code=400, detail=f"Unsupported language. Supported: {supported}."
        )

    try:
        result = review_code(
            language=request.language,
            code=request.code,
            program_input=request.input,
            program_output=request.output,
        )
    except AIReviewError as error:
        # The service decides the right status code (503 missing key, 502 upstream).
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    return {
        "review": result["review"],
        "model": result["model"],
        "reviewed_by": UserOut.from_row(current_user),
    }
