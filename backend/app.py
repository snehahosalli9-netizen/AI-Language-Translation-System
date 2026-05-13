"""Main FastAPI application for AI Language Translation System."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZIPMiddleware

from config import settings
from database.database import create_all_tables, SessionLocal
from routes import auth, translation, history, favorites, speech, analytics, admin
from ml.model_loader import ModelLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize ML models
model_loader = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global model_loader
    
    # Startup
    logger.info("🚀 Starting AI Language Translation System...")
    
    try:
        # Initialize database
        create_all_tables()
        logger.info("✅ Database initialized")
        
        # Load ML models
        logger.info("🤖 Loading machine learning models...")
        model_loader = ModelLoader()
        logger.info("✅ ML models loaded successfully")
        
        logger.info("🎉 Application startup complete!")
    except Exception as e:
        logger.error(f"❌ Startup error: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    logger.info("✅ Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title="AI Language Translation API",
    description="Machine Learning powered language translation system with REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZIP compression middleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Health check endpoint
@app.get("/api/health", tags=["Health Check"])
async def health_check():
    """Check API health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AI Language Translation System API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }


# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(translation.router, prefix="/api", tags=["Translation"])
app.include_router(history.router, prefix="/api", tags=["History"])
app.include_router(favorites.router, prefix="/api", tags=["Favorites"])
app.include_router(speech.router, prefix="/api", tags=["Speech"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
