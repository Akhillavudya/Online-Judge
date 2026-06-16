"""Request model for the AI code-review endpoint."""

from pydantic import BaseModel, Field


class AIReviewRequest(BaseModel):
    """Body for ``POST /ai/review``."""

    language: str = "cpp"
    code: str = Field(min_length=1)
    input: str | None = None
    output: str | None = None
