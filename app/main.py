from contextlib import asynccontextmanager
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import router
from app.core.config import settings
from app.core.exceptions import BaseAuthException
from app.core.logging import SensitiveDataFilter
from app.core.rate_limiter import limiter

# Configure logging with sensitive data masking filter
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
log_handler = logging.StreamHandler()
log_handler.addFilter(SensitiveDataFilter())
logger.addHandler(log_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} starting...")
    yield
    logger.info("👋 Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready e-commerce backend API with AI integration",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate Limiter ─────────────────────────────────────────────────────────────
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
        },
    )


# ── Custom Auth Exception Handlers ──────────────────────────────────────────
@app.exception_handler(BaseAuthException)
async def custom_auth_exception_handler(request: Request, exc: BaseAuthException) -> JSONResponse:
    content: dict[str, Any] = {
        "success": False,
        "code": exc.code,
        "message": exc.message,
    }
    if exc.details is not None:
        content["details"] = exc.details

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(content),
    )


# ── Pydantic Request Validation Error Handler ────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Check if a BaseAuthException was raised inside Pydantic validator
    for err in exc.errors():
        ctx = err.get("ctx", {})
        if "error" in ctx and isinstance(ctx["error"], BaseAuthException):
            base_exc: BaseAuthException = ctx["error"]
            content: dict[str, Any] = {
                "success": False,
                "code": base_exc.code,
                "message": base_exc.message,
            }
            if base_exc.details is not None:
                content["details"] = base_exc.details
            return JSONResponse(status_code=base_exc.status_code, content=jsonable_encoder(content))

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({
            "success": False,
            "code": "VALIDATION_ERROR",
            "message": "Invalid request parameters.",
            "details": exc.errors(),
        }),
    )


# ── Global Unhandled Exception Handler ───────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred.",
        },
    )


# ── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(router, prefix=settings.API_V1_STR)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "message": f"{settings.PROJECT_NAME} is running",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
