"""
Global FastAPI Exception Handlers
Registers handlers for custom payment exceptions
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from apps.payments.exceptions import PaymentError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with FastAPI app.
    
    Usage:
        app = FastAPI()
        register_exception_handlers(app)
    """
    
    @app.exception_handler(PaymentError)
    async def payment_error_handler(request: Request, exc: PaymentError):
        """Handle all payment-related exceptions."""
        logger.error(
            f"Payment error: {exc.error_code} - {exc.message}",
            extra={
                "error_code": exc.error_code,
                "path": request.url.path,
                "method": request.method,
                "details": exc.details
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": errors}
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        logger.exception(f"Unhandled error: {str(exc)}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {} if app.debug else {"trace_id": "generate-trace-id"}
                }
            }
        )


# Standalone handler functions for direct use
async def payment_exception_handler(request: Request, exc: PaymentError):
    """Standalone handler for PaymentError."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )
