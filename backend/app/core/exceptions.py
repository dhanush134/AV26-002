from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


class NotFoundError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class BadRequestError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


def error_response(status_code: int, message: str, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return error_response(status.HTTP_404_NOT_FOUND, exc.message, "not_found")

    @app.exception_handler(BadRequestError)
    async def bad_request_handler(_: Request, exc: BadRequestError) -> JSONResponse:
        return error_response(status.HTTP_400_BAD_REQUEST, exc.message, "bad_request")

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_handler(_: Request, __: SQLAlchemyError) -> JSONResponse:
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "A database error occurred while processing the request.",
            "database_error",
        )
