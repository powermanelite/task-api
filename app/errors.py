from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _format_validation_error(exc: RequestValidationError) -> str:
    parts = []
    for err in exc.errors():
        # Drop the leading "body"/"query"/"path" segment and any numeric
        # positions (e.g. a JSON parse error offset) for readability.
        fields = [str(p) for p in err["loc"][1:] if isinstance(p, str)]
        msg = err["msg"].removeprefix("Value error, ")
        if fields:
            parts.append(f"{'.'.join(fields)}: {msg}")
        elif err["loc"][0] == "body" and len(err["loc"]) == 1:
            parts.append(f"body: {msg}")
        else:
            parts.append(msg)
    return "; ".join(parts)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        # Covers explicit HTTPExceptions and router-level 404/405.
        detail = exc.detail
        if exc.status_code == 404 and detail == "Not Found":
            detail = f"Route not found: {request.method} {request.url.path}"
        return JSONResponse(
            {"detail": detail},
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse({"detail": _format_validation_error(exc)}, status_code=422)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        return JSONResponse({"detail": "Internal server error"}, status_code=500)
