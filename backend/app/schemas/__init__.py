"""Pydantic models describing what each endpoint accepts and returns.

Request models (e.g. ``RegisterRequest``) validate incoming JSON before a router
runs. Response models (e.g. ``UserOut``) shape the JSON we send back so the
output stays stable for the frontend.
"""
