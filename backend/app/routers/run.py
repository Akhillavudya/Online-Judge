"""The code-execution endpoint: compile and run submitted C++ code."""

from fastapi import APIRouter, HTTPException

from app.schemas.run import RunRequest
from app.services.executor import execute_cpp
from app.services.file_manager import generate_file

router = APIRouter(tags=["run"])

SUPPORTED_LANGUAGE = "cpp"


@router.post("/run")
async def run_code(request: RunRequest):
    """Write the code to disk, compile & run it, and return the program output."""
    # Reject empty programs before touching the filesystem.
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Empty code!")

    # Only the C++ executor exists today.
    if request.language != SUPPORTED_LANGUAGE:
        raise HTTPException(status_code=400, detail="Only C++ is supported right now.")

    try:
        file_path = generate_file(request.language, request.code)
        output = execute_cpp(file_path, request.input)
        return {"filePath": file_path, "output": output}
    except RuntimeError as error:
        # Compiler/runtime failures (incl. the executor's stderr) become a 500.
        raise HTTPException(status_code=500, detail=str(error)) from error
