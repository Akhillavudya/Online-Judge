"""Authentication endpoints: register, login, current user, and logout."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.security import generate_token_value, hash_password, verify_password
from app.db.repositories import tokens, users
from app.dependencies import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(user_id: int) -> str:
    """Create a new token for ``user_id`` and persist it."""
    token = generate_token_value()
    tokens.insert_token(token, user_id)
    return token


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    """Create a new account and return a token plus the public user record."""
    try:
        user = users.create_user(
            name=request.name.strip(),
            email=request.email.lower(),
            password_hash=hash_password(request.password),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Email already registered.") from error

    return {"token": _issue_token(user["id"]), "user": UserOut.from_row(user)}


@router.post("/login")
def login(request: LoginRequest):
    """Verify credentials and return a fresh token plus the public user record."""
    user = users.get_user_by_email(request.email.lower())
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {"token": _issue_token(user["id"]), "user": UserOut.from_row(user)}


@router.get("/me")
def me(current_user: Annotated[sqlite3.Row, Depends(get_current_user)]):
    """Return the currently authenticated user."""
    return {"user": UserOut.from_row(current_user)}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(authorization: Annotated[str | None, Header()] = None):
    """Invalidate the caller's token. Always succeeds, even without a valid token."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        tokens.delete_token(token)
