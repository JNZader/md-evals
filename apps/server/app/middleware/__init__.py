"""Middleware: auth dependency, CORS."""

from app.middleware.auth import CurrentUser, get_current_user

__all__ = ["CurrentUser", "get_current_user"]
