"""Profile & leaderboard endpoints (Phase 7).

These are read-only, aggregation-driven views built on top of the judging data:

    GET /leaderboard            -> users ranked by problems solved
    GET /users/{id}/profile     -> one user's public stats + recent activity

Both require a logged-in user (like the rest of the API) but show *public*
information — any signed-in user can view anyone's profile and the leaderboard.
All the heavy lifting (the ``GROUP BY`` / ``COUNT`` queries) lives in
``db/repositories/stats.py``; the router just assembles the response shapes and
assigns the 1-based ranks.
"""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.repositories import stats, users
from app.dependencies import get_current_user
from app.schemas.judge import UserSubmissionOut
from app.schemas.stats import (
    LeaderboardEntryOut,
    ProfileOut,
    SolvedByDifficulty,
)

router = APIRouter(tags=["stats"])


@router.get("/leaderboard")
def get_leaderboard(
    _current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Return the top solvers, ranked by number of problems solved.

    The repository orders the rows; here we just number them 1..N (`enumerate`)
    so ties share the SQL ordering, not the rank.
    """
    rows = stats.get_leaderboard(limit=limit)
    leaderboard = [
        LeaderboardEntryOut(
            rank=index + 1,
            user_id=row["user_id"],
            name=row["name"],
            solved_count=row["solved_count"],
            submission_count=row["submission_count"],
        )
        for index, row in enumerate(rows)
    ]
    return {"leaderboard": leaderboard}


@router.get("/users/{user_id}/profile")
def get_user_profile(
    user_id: int,
    _current_user: Annotated[sqlite3.Row, Depends(get_current_user)],
):
    """Return a user's public profile: identity + solving stats + recent activity."""
    user = users.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    submission_stats = stats.get_user_submission_stats(user_id)
    breakdown = stats.get_user_solved_by_difficulty(user_id)
    recent = stats.get_recent_submissions(user_id, limit=10)

    return ProfileOut(
        user_id=user["id"],
        name=user["name"],
        role=user["role"],
        created_at=user["created_at"],
        total_solved=submission_stats["total_solved"],
        total_submissions=submission_stats["total_submissions"],
        accepted_submissions=submission_stats["accepted_submissions"],
        solved_by_difficulty=SolvedByDifficulty(**breakdown),
        recent_submissions=[UserSubmissionOut.from_row(row) for row in recent],
    )
