"""Promote (or demote) a user by email — the only way to grant the admin role.

There is deliberately **no HTTP endpoint** that lets a user make themselves an
admin; that would defeat the purpose. Instead an operator runs this script on the
server, where they already have shell access:

    python make_admin.py akhil@example.com            # make this user an admin
    python make_admin.py akhil@example.com --role user  # demote back to a normal user

It prints the user's new role, or an error if no account has that email.
"""

import argparse

from app.db.database import init_database
from app.db.repositories import users


def main() -> None:
    parser = argparse.ArgumentParser(description="Set a user's role by email.")
    parser.add_argument("email", help="Email of the account to update.")
    parser.add_argument(
        "--role",
        choices=["admin", "user"],
        default="admin",
        help="Role to assign (default: admin).",
    )
    args = parser.parse_args()

    # Make sure the schema (incl. the role column / migration) exists first.
    init_database()

    user = users.get_user_by_email(args.email.lower())
    if not user:
        print(f"No user found with email {args.email!r}.")
        raise SystemExit(1)

    updated = users.set_user_role(user["id"], args.role)
    print(f"{updated['email']} is now '{updated['role']}'.")


if __name__ == "__main__":
    main()
