"""FastAPI application main entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uvicorn

from ..utils.config.settings import settings
from ..utils.database.postgres_client import postgres_client
from ..utils.database.mongo_client import mongo_client
from ..utils.database.redis_client import redis_client
from .routes import audiences, health, scoring, synthetic
from .middleware.logging_middleware import LoggingMiddleware
from .middleware.auth_middleware import AuthMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Intent Audience API...")
    
    try:
        # Initialize database connections
        await postgres_client.initialize()
        await mongo_client.initialize()
        await redis_client.initialize()
        logger.info("Database connections initialized")
        
        # Perform health checks
        postgres_healthy = await postgres_client.health_check()
        mongo_healthy = await mongo_client.health_check()
        redis_healthy = await redis_client.health_check()
        
        if not all([postgres_healthy, mongo_healthy, redis_healthy]):
            logger.warning("Some database connections are unhealthy")
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Intent Audience API...")
    
    try:
        await postgres_client.close()
        await mongo_client.close()
        await redis_client.close()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="ML Intent-Based Audience Pipeline API",
    description="API for generating and managing customer audiences based on ML intent predictions",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error processing {request.method} {request.url}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An internal server error occurred",
            "timestamp": time.time()
        }
    )


# Include routers
app.include_router(
    health.router,
    prefix="/v1",
    tags=["System"]
)

app.include_router(
    audiences.router,
    prefix="/v1",
    tags=["Audiences"]
)

app.include_router(
    scoring.router,
    prefix="/v1",
    tags=["Intent Scoring"]
)

app.include_router(
    synthetic.router,
    prefix="/v1",
    tags=["Synthetic Data"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": "ML Intent-Based Audience Pipeline API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "health": "/v1/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )