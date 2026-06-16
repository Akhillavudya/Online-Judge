"""Health-check endpoint used to confirm the API is online."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
def health_check():
    """Return a tiny payload so the frontend/developer can verify the API is up."""
    return {"online": "compiler"}
