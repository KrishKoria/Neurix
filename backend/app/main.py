"""
Main FastAPI application with modular structure and optimizations.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import settings
from app.core.database import init_database_with_retry, close_database_connections
from app.utils.logging import setup_logging
from app.utils.performance import performance_monitor, db_monitor

# Import routers
from app.routers import (
    health_router,
    users_router,
    groups_router,
    expenses_router,
    chatbot_router
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Splitwise API...")
    logger.info(f"📋 Configuration: {settings.api_title} v{settings.api_version}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    logger.info(f"🤖 AI Chatbot: {'enabled' if settings.deepseek_api_key else 'disabled (fallback mode)'}")
    
    # Initialize database
    logger.info("🗄️ Initializing database connection...")
    db_success = init_database_with_retry()
    if not db_success:
        logger.error("❌ Failed to initialize database. Some features may not work.")
    else:
        logger.info("✅ Database initialized successfully")
    
    logger.info("🎯 API startup complete!")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down Splitwise API...")
    close_database_connections()
    logger.info("✅ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Monitor request performance and add timing headers."""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Add performance headers
    response.headers["X-Process-Time"] = str(round(process_time, 2))
    response.headers["X-API-Version"] = settings.api_version
    
    # Record metrics
    performance_monitor.record_metric(
        "request_duration",
        process_time,
        {
            "method": request.method,
            "endpoint": str(request.url.path),
            "status_code": str(response.status_code)
        }
    )
    
    # Log slow requests
    if process_time > 1000:  # > 1 second
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}ms")
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions gracefully."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Exception",
                "detail": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    # For non-HTTP exceptions, return a generic error
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
            "type": type(exc).__name__ if settings.debug else "ServerError"
        }
    )


# Rate limiting (simple implementation)
from collections import defaultdict
from datetime import datetime, timedelta

request_counts = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware."""
    if not settings.debug:  # Only apply in production
        client_ip = request.client.host
        now = datetime.now()
        
        # Clean old requests (older than 1 minute)
        request_counts[client_ip] = [
            req_time for req_time in request_counts[client_ip]
            if req_time > now - timedelta(minutes=1)
        ]
        
        # Check rate limit (100 requests per minute)
        if len(request_counts[client_ip]) > 100:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate Limit Exceeded",
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": 60
                }
            )
        
        # Record this request
        request_counts[client_ip].append(now)
    
    return await call_next(request)


# Include routers with API versioning
API_V1_PREFIX = "/api/v1"

app.include_router(health_router)  # No prefix for health endpoints
app.include_router(users_router, prefix=API_V1_PREFIX)
app.include_router(groups_router, prefix=API_V1_PREFIX)
app.include_router(expenses_router, prefix=API_V1_PREFIX)
app.include_router(chatbot_router, prefix=API_V1_PREFIX)


# Additional endpoints for monitoring
@app.get("/metrics", tags=["monitoring"])
def get_metrics():
    """Get application performance metrics."""
    return {
        "performance": performance_monitor.get_all_metrics(),
        "database": db_monitor.get_stats(),
        "system": {
            "api_version": settings.api_version,
            "debug": settings.debug,
            "features": {
                "ai_chatbot": bool(settings.deepseek_api_key),
                "caching": True,
                "rate_limiting": not settings.debug
            }
        }
    }


# Legacy endpoints for backward compatibility
@app.post("/users", include_in_schema=False)
@app.get("/users", include_in_schema=False)
@app.get("/users/{user_id}", include_in_schema=False)
@app.get("/users/{user_id}/balances", include_in_schema=False)
@app.post("/groups", include_in_schema=False)
@app.get("/groups", include_in_schema=False)
@app.get("/groups/{group_id}", include_in_schema=False)
@app.get("/groups/{group_id}/balances", include_in_schema=False)
@app.post("/groups/{group_id}/expenses", include_in_schema=False)
@app.post("/chatbot", include_in_schema=False)
async def legacy_endpoint_redirect(request: Request):
    """Redirect legacy endpoints to versioned API."""
    new_path = f"{API_V1_PREFIX}{request.url.path}"
    logger.info(f"Redirecting legacy endpoint {request.url.path} to {new_path}")
    
    return JSONResponse(
        status_code=308,  # Permanent redirect
        content={
            "message": "This endpoint has moved",
            "new_endpoint": new_path,
            "note": "Please update your client to use the versioned API endpoints"
        },
        headers={"Location": new_path}
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Splitwise API server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )
