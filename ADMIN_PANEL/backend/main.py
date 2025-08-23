"""
SCUM Bot Admin Panel - FastAPI Main Application
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_database, close_database

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    await init_database()
    logger.info("✅ Database initialized")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down application")
    await close_database()
    logger.info("✅ Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Panel administrativo web para el bot SCUM Discord",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*"] if settings.DEBUG else ["yourdomain.com"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": f"🤖 {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs" if settings.DEBUG else None
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "debug_mode": settings.DEBUG,
        "database": "connected"
    }

# Include routers
from app.auth.routes import router as auth_router
from app.modules.fame.routes import router as fame_router
# from app.modules.taxi.routes import taxi_router

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(fame_router, prefix=f"{settings.API_V1_STR}/fame", tags=["fame-points"])
# app.include_router(taxi_router, prefix=f"{settings.API_V1_STR}/taxi", tags=["taxi-system"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )