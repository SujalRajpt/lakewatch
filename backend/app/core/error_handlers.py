import math

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def sanitize_error(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, float) and not math.isfinite(value):
        return str(value)

    if isinstance(value, dict):
        return {key: sanitize_error(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [sanitize_error(item) for item in value]

    return value


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={"detail": sanitize_error(exc.errors())},
    )
