"""Error handling module for the API."""
from typing import Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIError(HTTPException):
    """Base class for API errors."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        error_type: str
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.error_type = error_type


class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource: str, resource_id: Any) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {resource_id} not found",
            error_code="RESOURCE_NOT_FOUND",
            error_type="not_found"
        )


class DatabaseError(APIError):
    """Raised when a database operation fails."""
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR",
            error_type="database"
        )


class ValidationError(APIError):
    """Raised when request validation fails."""
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR",
            error_type="validation"
        )


class BusinessLogicError(APIError):
    """Raised when a business rule is violated."""
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BUSINESS_LOGIC_ERROR",
            error_type="business_logic"
        )


async def api_error_handler(
    request: Request,
    exc: APIError
) -> JSONResponse:
    """Handle API errors and return formatted error response."""
    error_response = {
        "error": {
            "code": exc.error_code,
            "type": exc.error_type,
            "message": exc.detail,
            "path": request.url.path
        }
    }
    # Log the error
    logger.error(
        "API Error: %s - %s - %s",
        exc.error_code,
        exc.detail,
        request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy errors."""
    error = DatabaseError(f"Database error occurred: {str(exc)}")
    return await api_error_handler(request, error)


async def validation_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """Handle validation errors."""
    if exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        error = ValidationError(str(exc.detail))
        return await api_error_handler(request, error)
    return await api_error_handler(
        request,
        APIError(
            status_code=exc.status_code,
            detail=str(exc.detail),
            error_code="UNKNOWN_ERROR",
            error_type="unknown"
        )
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle any unhandled exceptions."""
    logger.exception("Unhandled exception occurred")
    error = APIError(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred",
        error_code="INTERNAL_SERVER_ERROR",
        error_type="server_error"
    )
    return await api_error_handler(request, error)
