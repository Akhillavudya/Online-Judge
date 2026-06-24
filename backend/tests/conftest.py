"""Shared pytest fixtures for the backend test suite.

Every test runs against a **fresh, isolated SQLite database** in a temp folder, so
tests never see each other's users, problems, or submissions. The fixtures here
also give tests easy ways to register a user, get an admin, and seed a problem
with test cases, so the individual test files stay short and readable.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make the backend package importable even if pytest is launched from elsewhere.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings  # noqa: E402
from app.db.database import init_database  # noqa: E402
from app.db.repositories import users  # noqa: E402
from app.main import app  # noqa: E402
from app.services import rate_limit  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A ``TestClient`` backed by a brand-new database in a temp directory.

    Pointing ``settings.DATABASE_PATH`` (and the code/output work folders) at a
    per-test temp path means each test starts from an empty schema. The rate
    limiters are disabled so a test can submit many times without tripping the
    per-minute cap.
    """
    monkeypatch.setattr(settings, "DATABASE_PATH", tmp_path / "test.db")

    codes_dir = tmp_path / "codes"
    outputs_dir = tmp_path / "outputs"
    codes_dir.mkdir()
    outputs_dir.mkdir()
    monkeypatch.setattr(settings, "CODES_DIR", codes_dir)
    monkeypatch.setattr(settings, "OUTPUTS_DIR", outputs_dir)

    # Disable rate limiting for tests (these singletons are shared by the routers).
    monkeypatch.setattr(rate_limit.run_rate_limit, "enabled", False)
    monkeypatch.setattr(rate_limit.submit_rate_limit, "enabled", False)

    init_database()
    return TestClient(app)


@pytest.fixture
def register(client):
    """Return a helper that registers a user and yields auth headers + the user.

    Usage::

        headers, user = register()                 # default test user
        headers, user = register(email="a@b.com")  # a second, distinct user
    """
    counter = {"n": 0}

    def _register(name="Test User", email=None, password="secret123"):
        if email is None:
            counter["n"] += 1
            email = f"user{counter['n']}@example.com"
        response = client.post(
            "/auth/register",
            json={"name": name, "email": email, "password": password},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        headers = {"Authorization": f"Bearer {body['token']}"}
        return headers, body["user"]

    return _register


@pytest.fixture
def admin(register):
    """Register a user and promote them to admin, returning (headers, user).

    Promotion goes straight through the repository (the same path
    ``make_admin.py`` uses) because there is intentionally no self-promote
    endpoint. The existing token keeps working — the role is read fresh on each
    request.
    """
    headers, user = register(name="Admin", email="admin@example.com")
    users.set_user_role(user["id"], "admin")
    return headers, user


@pytest.fixture
def make_problem(client, admin):
    """Return a helper that creates a problem (with test cases) via the admin API.

    Defaults to a simple "add two numbers" problem with one sample and one hidden
    test case. Returns the created problem's slug.
    """
    admin_headers, _ = admin

    def _make_problem(
        title="Add Two Numbers",
        statement="Read two integers and print their sum.",
        test_cases=None,
        **overrides,
    ):
        if test_cases is None:
            test_cases = [
                {"input": "3 4\n", "expected_output": "7", "is_sample": True},
                {"input": "10 20\n", "expected_output": "30", "is_sample": False},
            ]
        payload = {
            "title": title,
            "statement": statement,
            "difficulty": "easy",
            "test_cases": test_cases,
            **overrides,
        }
        response = client.post("/admin/problems", json=payload, headers=admin_headers)
        assert response.status_code == 201, response.text
        return response.json()["problem"]["slug"]

    return _make_problem
