from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.core.config import settings


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


app = FastAPI(title="Arvexo Account API", version="0.1.0", debug=not settings.is_production)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
        return error_response(exc.status_code, exc.detail["code"], exc.detail["message"])
    return error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    message = str(first.get("msg", "Validation error"))
    return error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", message)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    if settings.is_production:
        return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "Internal server error")
    return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", str(exc))


app.include_router(health_router)
app.include_router(auth_router)
