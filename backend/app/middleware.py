"""API key authentication middleware."""

import os

from fastapi import Request, Response
from starlette.responses import JSONResponse

API_KEY = os.environ.get("FORGE_API_KEY")

OPEN_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}


async def api_key_middleware(request: Request, call_next) -> Response:
    if not API_KEY:
        return await call_next(request)

    if request.url.path in OPEN_PATHS:
        return await call_next(request)

    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if key != API_KEY:
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})

    return await call_next(request)
