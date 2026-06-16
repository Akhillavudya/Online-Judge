"""Routers: the HTTP layer.

Each module groups related endpoints with an :class:`fastapi.APIRouter`. Routers
stay thin — they read the request, call a service or repository, and return the
result. They never contain SQL or third-party API calls directly.
"""
