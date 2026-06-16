"""Seed the database with a few example problems and test cases.

Run from the backend folder once (it is safe to re-run — existing problems are
skipped by slug):

    python seed_problems.py

Each problem lists its test cases as ``(input, expected_output, is_sample)``.
Sample cases (is_sample=True) are shown on the problem page; the rest stay hidden
and will be used by the judge in Phase 2.
"""

from app.db.database import init_database
from app.db.repositories import problems, test_cases

SEED_PROBLEMS = [
    {
        "title": "A + B Problem",
        "statement": (
            "Given two integers A and B, print their sum.\n\n"
            "This is the classic warm-up problem found on almost every judge."
        ),
        "input_format": "A single line containing two space-separated integers A and B.",
        "output_format": "A single integer: the value of A + B.",
        "constraints": "-10^9 <= A, B <= 10^9",
        "difficulty": "easy",
        "test_cases": [
            ("5 7", "12", True),
            ("-3 3", "0", True),
            ("1000000000 1000000000", "2000000000", False),
            ("-1000000000 -5", "-1000000005", False),
        ],
    },
    {
        "title": "Sum of an Array",
        "statement": (
            "You are given N integers. Print the sum of all of them.\n\n"
            "Read N, then read N integers and output their total."
        ),
        "input_format": "The first line contains N. The second line contains N space-separated integers.",
        "output_format": "A single integer: the sum of the N integers.",
        "constraints": "1 <= N <= 10^5",
        "difficulty": "easy",
        "test_cases": [
            ("3\n1 2 3", "6", True),
            ("5\n10 20 30 40 50", "150", True),
            ("1\n-7", "-7", False),
            ("4\n0 0 0 0", "0", False),
        ],
    },
    {
        "title": "Maximum of Three",
        "statement": (
            "Given three integers, print the largest one.\n\n"
            "A simple comparison problem to practice reading input and conditionals."
        ),
        "input_format": "A single line with three space-separated integers.",
        "output_format": "A single integer: the maximum of the three.",
        "constraints": "-10^9 <= each integer <= 10^9",
        "difficulty": "easy",
        "test_cases": [
            ("3 9 5", "9", True),
            ("-1 -7 -3", "-1", True),
            ("100 100 100", "100", False),
            ("0 -5 8", "8", False),
        ],
    },
]


def _slugify(title: str) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "problem"


def seed() -> None:
    init_database()

    created = 0
    skipped = 0
    for data in SEED_PROBLEMS:
        slug = _slugify(data["title"])
        if problems.slug_exists(slug):
            print(f"  skip   {slug} (already exists)")
            skipped += 1
            continue

        problem = problems.create_problem(
            title=data["title"],
            slug=slug,
            statement=data["statement"],
            input_format=data["input_format"],
            output_format=data["output_format"],
            constraints=data["constraints"],
            difficulty=data["difficulty"],
            time_limit_ms=2000,
            memory_limit_mb=256,
            created_by=None,
        )
        for input_text, expected_output, is_sample in data["test_cases"]:
            test_cases.create_test_case(
                problem_id=problem["id"],
                input_text=input_text,
                expected_output=expected_output,
                is_sample=is_sample,
            )
        print(f"  create {slug} ({len(data['test_cases'])} test cases)")
        created += 1

    print(f"\nDone. {created} created, {skipped} skipped.")


if __name__ == "__main__":
    seed()
