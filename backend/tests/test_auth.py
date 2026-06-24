"""Tests for the authentication endpoints (register / login / me)."""


def test_register_returns_token_and_user(client):
    response = client.post(
        "/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "secret123"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["token"]
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["role"] == "user"
    # The password hash must never be returned to the client.
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_register_duplicate_email_conflicts(client):
    payload = {"name": "Bob", "email": "bob@example.com", "password": "secret123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    # Same email a second time -> 409 Conflict.
    duplicate = client.post("/auth/register", json=payload)
    assert duplicate.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register",
        json={"name": "Eve", "email": "eve@example.com", "password": "short"},
    )
    assert response.status_code == 422  # fails the min_length=6 validation


def test_login_succeeds_with_correct_credentials(client, register):
    register(email="carol@example.com", password="secret123")
    response = client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "secret123"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["token"]


def test_login_fails_with_wrong_password(client, register):
    register(email="dave@example.com", password="secret123")
    response = client.post(
        "/auth/login",
        json={"email": "dave@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_me_requires_a_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_current_user_with_token(client, register):
    headers, user = register(email="frank@example.com")
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["user"]["email"] == "frank@example.com"
