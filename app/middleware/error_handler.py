"""Middleware para tratamento de erros."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handler para HTTPException.
    """
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail) if isinstance(exc.detail, str) else exc.detail,
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler para erros de validação Pydantic.
    """
    logger.error(f"Validation Error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_code": "VALIDATION_ERROR",
            "message": "Erros de validação nos dados fornecidos",
            "details": exc.errors()
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handler genérico para exceções não tratadas.
    """
    logger.error(f"Unexpected Error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Erro interno do servidor",
            "details": str(exc) if logger.level == logging.DEBUG else None
        }
    )
