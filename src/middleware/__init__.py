"""Middleware package for request processing."""

from .auth_middleware import auth_middleware

__all__ = ["auth_middleware"]
