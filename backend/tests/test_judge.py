"""End-to-end tests for the judging engine (the heart of the project).

These submit real code and assert on the resulting verdict. We use **Python** as
the language so the tests need only a Python interpreter (always present in CI),
not a C++ toolchain. The judge loop itself is language-agnostic, so exercising it
through Python still covers the AC / WA logic.
"""

# A correct solution to "read two integers, print their sum".
CORRECT_SOLUTION = "a, b = map(int, input().split())\nprint(a + b)\n"

# A wrong solution: prints the difference instead of the sum.
WRONG_SOLUTION = "a, b = map(int, input().split())\nprint(a - b)\n"


def _submit(client, slug, headers, code, language="python"):
    return client.post(
        f"/problems/{slug}/submit",
        json={"language": language, "code": code},
        headers=headers,
    )


def test_correct_solution_gets_accepted(client, register, make_problem):
    slug = make_problem()
    headers, _ = register(email="solver@example.com")

    response = _submit(client, slug, headers, CORRECT_SOLUTION)
    assert response.status_code == 200, response.text

    result = response.json()["result"]
    assert result["verdict"] == "AC"
    assert result["passed_count"] == result["total_count"]
    assert result["total_count"] == 2  # one sample + one hidden case


def test_wrong_solution_gets_wrong_answer(client, register, make_problem):
    slug = make_problem()
    headers, _ = register(email="wrong@example.com")

    response = _submit(client, slug, headers, WRONG_SOLUTION)
    assert response.status_code == 200, response.text

    result = response.json()["result"]
    assert result["verdict"] == "WA"
    # It fails the very first case, so nothing passed.
    assert result["passed_count"] == 0


def test_submit_requires_authentication(client, make_problem):
    slug = make_problem()
    response = _submit(client, slug, headers={}, code=CORRECT_SOLUTION)
    assert response.status_code == 401


def test_submit_rejects_unsupported_language(client, register, make_problem):
    slug = make_problem()
    headers, _ = register(email="lang@example.com")
    response = _submit(client, slug, headers, "print(1)", language="cobol")
    assert response.status_code == 400


def test_an_accepted_submission_shows_up_in_history(client, register, make_problem):
    slug = make_problem()
    headers, _ = register(email="history@example.com")
    _submit(client, slug, headers, CORRECT_SOLUTION)

    history = client.get(f"/problems/{slug}/submissions", headers=headers).json()
    assert history["total"] == 1
    assert history["submissions"][0]["verdict"] == "AC"
