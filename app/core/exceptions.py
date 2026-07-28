from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Base class for custom domain exceptions."""

    def __init__(
        self,
        message: str = "An error occurred.",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class UserAlreadyExistsError(DomainException):
    def __init__(self, message: str = "A user with this email already exists."):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class UserNotFoundError(DomainException):
    def __init__(self, message: str = "User not found."):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class InvalidCredentialsError(DomainException):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"headers": {"WWW-Authenticate": "Bearer"}},
        )


class AccountDisabledError(DomainException):
    def __init__(self, message: str = "User account is inactive or disabled."):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class EmailNotVerifiedError(DomainException):
    def __init__(self, message: str = "Email address has not been verified yet."):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class InvalidTokenError(DomainException):
    def __init__(self, message: str = "Invalid, expired, or revoked token.", status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(message=message, status_code=status_code)


class RateLimitExceededError(DomainException):
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register custom domain exception handlers on the FastAPI application instance."""

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        headers = exc.details.get("headers", {}) if exc.details else {}
        content: Dict[str, Any] = {
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code,
        }
        if exc.details and "headers" in exc.details:
            # exclude internal header metadata from body if present
            clean_details = {k: v for k, v in exc.details.items() if k != "headers"}
            if clean_details:
                content["details"] = clean_details
        elif exc.details:
            content["details"] = exc.details

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )
