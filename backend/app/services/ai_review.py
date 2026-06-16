"""Asks Google Gemini to review a piece of C++ code.

This service knows nothing about FastAPI. When something goes wrong it raises
:class:`AIReviewError` with a suggested HTTP status code, and the router decides
how to present that to the client.
"""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings

GEMINI_TIMEOUT_SECONDS = 30


class AIReviewError(Exception):
    """Raised when a code review cannot be produced.

    Carries the HTTP ``status_code`` the router should return along with a
    human-readable ``detail`` message.
    """

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _build_prompt(language: str, code: str, program_input: str | None, program_output: str | None) -> str:
    """Compose the reviewer prompt sent to Gemini."""
    return f"""
You are an expert C++ code reviewer for an online compiler.
Review the user's code with concise, practical feedback.
Mention correctness risks, edge cases, complexity, readability, and one improved snippet only if useful.
Keep the answer under 180 words.

Language: {language}
Input:
{program_input or "(none)"}

Program output:
{program_output or "(not run yet)"}

Code:
```cpp
{code}
```
"""


def review_code(
    language: str,
    code: str,
    program_input: str | None,
    program_output: str | None,
) -> dict:
    """Return ``{"review": ..., "model": ...}`` for the given code.

    Raises:
        AIReviewError: if the API key is missing, or Gemini returns an error or
            an empty response.
    """
    if not settings.GEMINI_API_KEY:
        raise AIReviewError(503, "GEMINI_API_KEY is not configured on the backend.")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": _build_prompt(language, code, program_input, program_output)},
                ],
            },
        ],
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 512,
        },
    }
    model = settings.GEMINI_MODEL
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={settings.GEMINI_API_KEY}"
    )

    try:
        gemini_request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(gemini_request, timeout=GEMINI_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8") or str(error)
        raise AIReviewError(502, f"Gemini review failed: {detail}") from error
    except (URLError, TimeoutError) as error:
        raise AIReviewError(502, f"Gemini review failed: {error}") from error

    review = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
        .strip()
    )
    if not review:
        raise AIReviewError(502, "Gemini returned an empty review.")

    return {"review": review, "model": model}
