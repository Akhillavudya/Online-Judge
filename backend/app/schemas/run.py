"""Request model for the code-execution endpoint."""

from pydantic import BaseModel


class RunRequest(BaseModel):
    """Body for ``POST /run``."""

    # Selected language. Only C++ runs today, so the default matches the frontend.
    language: str = "cpp"

    # The source code to compile and run.
    code: str

    # Optional text piped to the program's standard input.
    input: str = ""
