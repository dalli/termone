"""FastAPI application initialization."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.database import get_db, init_db, close_db
from src.exceptions import TermoneException
from src.schemas import HealthCheckResponse
from src.api.hosts import router as hosts_router
from src.api.terminal import router as terminal_router
from src.api.stats import router as stats_router
from src.api.files import router as files_router
from src.api.tunnels import router as tunnels_router
from src.api.snippets import router as snippets_router
from src.api.admin import router as admin_router

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Termone API",
    description="Web-based SSH Infrastructure Management Platform",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(hosts_router, prefix="/api", tags=["hosts"])
app.include_router(terminal_router, prefix="/api", tags=["terminal"])
app.include_router(stats_router, prefix="/api", tags=["stats"])
app.include_router(files_router, prefix="/api", tags=["files"])
app.include_router(tunnels_router, prefix="/api", tags=["tunnels"])
app.include_router(snippets_router, prefix="/api", tags=["snippets"])
app.include_router(admin_router, prefix="/api", tags=["admin"])


# Exception handlers
@app.exception_handler(TermoneException)
async def termone_exception_handler(request, exc: TermoneException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "code": exc.code,
                "field": getattr(exc, "field", None),
            },
        },
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check(db=Depends(get_db)):
    """Health check endpoint."""
    try:
        return HealthCheckResponse(
            status="healthy",
            version="0.1.0",
            database="connected",
        )
    except Exception:
        return HealthCheckResponse(
            status="degraded",
            version="0.1.0",
            database="disconnected",
        )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database on shutdown."""
    await close_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        workers=settings.BACKEND_WORKERS,
        reload=settings.DEBUG,
    )
