"""Repositories: every SQL query lives in one of these modules.

Routers and services call these functions instead of writing SQL inline, so the
data-access code is centralised and the rest of the app stays free of database
details.
"""
