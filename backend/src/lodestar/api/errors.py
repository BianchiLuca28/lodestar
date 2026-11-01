"""Map domain errors to HTTP responses with a message key the UI translates."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from lodestar.domain.errors import Conflict, DomainError, FieldError, NotFound


class ErrorResponse(BaseModel):
    key: str
    field: str | None = None
    message: str


def _status(exc: DomainError) -> int:
    if isinstance(exc, NotFound):
        return 404
    if isinstance(exc, Conflict):
        return 409
    return 422


async def _handle(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    body = ErrorResponse(
        key=exc.key,
        field=exc.field if isinstance(exc, FieldError) else None,
        message=str(exc),
    )
    return JSONResponse(status_code=_status(exc), content=body.model_dump())


def install(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle)
