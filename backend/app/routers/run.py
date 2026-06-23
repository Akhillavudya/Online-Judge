"""The code-execution endpoint: compile and run submitted code (C++ or Python)."""

from fastapi import APIRouter, HTTPException

from app.schemas.run import RunRequest
from app.services.executor import execute_code
from app.services.file_manager import generate_file
from app.services.languages import SUPPORTED_LANGUAGES, get_language

router = APIRouter(tags=["run"])


@router.post("/run")
async def run_code(request: RunRequest):
    """Write the code to disk, compile & run it, and return the program output."""
    # Reject empty programs before touching the filesystem.
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Empty code!")

    if request.language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise HTTPException(
            status_code=400, detail=f"Unsupported language. Supported: {supported}."
        )

    try:
        file_path = generate_file(get_language(request.language).extension, request.code)
        output = execute_code(request.language, file_path, request.input)
        return {"filePath": file_path, "output": output}
    except RuntimeError as error:
        # Compiler/runtime failures (incl. the executor's stderr) become a 500.
        raise HTTPException(status_code=500, detail=str(error)) from error
