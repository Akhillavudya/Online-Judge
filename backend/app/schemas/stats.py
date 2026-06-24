"""Response models for the profile & leaderboard endpoints (Phase 7)."""

from pydantic import BaseModel

from app.schemas.judge import UserSubmissionOut


class SolvedByDifficulty(BaseModel):
    """How many problems a user has solved, split by difficulty."""

    easy: int = 0
    medium: int = 0
    hard: int = 0


class ProfileOut(BaseModel):
    """A user's public profile: identity + aggregated solving stats.

    Built in the router from several repository calls (basic user row, the
    difficulty breakdown, the submission counts, and a short recent-activity
    list) rather than a single row, so there is no ``from_row`` here.
    """

    user_id: int
    name: str
    role: str
    created_at: str

    total_solved: int
    total_submissions: int
    accepted_submissions: int
    solved_by_difficulty: SolvedByDifficulty
    recent_submissions: list[UserSubmissionOut]


class LeaderboardEntryOut(BaseModel):
    """One row of the leaderboard: a user and their solving totals.

    ``rank`` is 1-based and assigned in the router after ordering (the SQL only
    sorts; it does not number the rows).
    """

    rank: int
    user_id: int
    name: str
    solved_count: int
    submission_count: int
