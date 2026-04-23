"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.core.config import get_settings
from backend.api.routes import generation, history, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    settings = get_settings()
    print(f"Audora Backend Starting - Debug: {settings.DEBUG}")
    print(f"Allowed Origins: {settings.ALLOWED_ORIGINS}")
    yield
    # Shutdown
    print("Audora Backend Shutting Down")


# Create FastAPI app
app = FastAPI(
    title="Audora Backend API",
    description="Backend API for Audora - Automated Lecture Synthesis",
    version="0.1.0",
    lifespan=lifespan,
)

# Get settings for CORS configuration
settings = get_settings()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generation.router)
app.include_router(history.router)
app.include_router(profile.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Audora Backend API",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "debug": settings.DEBUG,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
