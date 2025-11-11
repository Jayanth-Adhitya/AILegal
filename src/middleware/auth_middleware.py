"""Authentication middleware to enforce authentication on all routes."""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Routes that don't require authentication
UNPROTECTED_ROUTES = [
    "/api/auth/login",
    "/api/auth/register",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce authentication on all API routes."""

    async def dispatch(self, request: Request, call_next):
        """Check authentication before processing request."""

        # Skip auth check for unprotected routes
        path = request.url.path
        if any(path.startswith(route) for route in UNPROTECTED_ROUTES):
            return await call_next(request)

        # Check session cookie
        session_id = request.cookies.get("session_id")
        if not session_id:
            logger.warning(f"Unauthenticated request to {path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required. Please log in."}
            )

        # Validate session using auth service
        # Note: auth_service will be injected into request state by the API layer
        # For now, we just check if the cookie exists
        # The actual validation happens in the endpoint handlers

        # Continue processing
        return await call_next(request)


# Factory function to create middleware instance
def auth_middleware():
    """Create authentication middleware instance."""
    return AuthMiddleware
