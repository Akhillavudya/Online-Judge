"""Tests for browsing problems and the admin-only create path (authorization)."""


def test_list_problems_starts_empty(client):
    response = client.get("/problems")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["problems"] == []
    assert body["total"] == 0


def test_regular_user_cannot_create_a_problem(client, register):
    headers, _ = register()
    response = client.post(
        "/admin/problems",
        json={"title": "Sneaky", "statement": "nope", "test_cases": []},
        headers=headers,
    )
    # Authenticated but not an admin -> 403 (authorization, not authentication).
    assert response.status_code == 403


def test_creating_a_problem_requires_authentication(client):
    response = client.post(
        "/admin/problems",
        json={"title": "Anon", "statement": "nope", "test_cases": []},
    )
    assert response.status_code == 401


def test_admin_creates_a_problem_and_it_appears_in_the_list(client, make_problem):
    slug = make_problem(title="Add Two Numbers")

    listing = client.get("/problems").json()
    assert listing["total"] == 1
    assert listing["problems"][0]["slug"] == slug


def test_problem_detail_exposes_only_sample_test_cases(client, make_problem):
    """The hidden test cases used for judging must never leak through the API."""
    slug = make_problem(
        test_cases=[
            {"input": "1 1\n", "expected_output": "2", "is_sample": True},
            {"input": "100 1\n", "expected_output": "101", "is_sample": False},
        ]
    )

    problem = client.get(f"/problems/{slug}").json()["problem"]
    samples = problem["sample_test_cases"]
    assert len(samples) == 1
    assert samples[0]["input"] == "1 1\n"
    # The hidden case's input/expected output must not be present anywhere.
    assert all(case["input"] != "100 1\n" for case in samples)


def test_unknown_problem_returns_404(client):
    assert client.get("/problems/does-not-exist").status_code == 404
