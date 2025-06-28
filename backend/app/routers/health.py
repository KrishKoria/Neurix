"""
Health check and system status routes.
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import health_check_dependency, get_cache_manager
from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/", summary="Root endpoint")
def root():
    """Root endpoint showing API status."""
    return {
        "message": "Splitwise API is running!",
        "status": "healthy",
        "version": settings.api_version
    }


@router.get("/health", response_model=HealthResponse, summary="Health check")
def health_check(health_data: dict = Depends(health_check_dependency)):
    """
    Comprehensive health check endpoint.
    
    Returns:
    - Database connection status
    - Connection pool information
    - API status
    """
    return HealthResponse(**health_data)


@router.get("/info", summary="System information")
def system_info(cache_manager = Depends(get_cache_manager)):
    """
    Get system information and configuration.
    
    Returns:
    - API version and configuration
    - Feature flags
    - Cache status
    """
    return {
        "api": {
            "title": settings.api_title,
            "version": settings.api_version,
            "description": settings.api_description,
            "debug": settings.debug
        },
        "features": {
            "ai_chatbot": bool(settings.deepseek_api_key),
            "caching": True,
            "database_optimizations": True
        },
        "cache": {
            "enabled": True,
            "type": "in_memory",
            "balance_cache_ttl": settings.balance_cache_ttl,
            "chatbot_cache_ttl": settings.chatbot_response_cache_ttl
        },
        "performance": {
            "max_concurrent_requests": settings.max_concurrent_requests,
            "request_timeout": settings.request_timeout,
            "database_pool_size": settings.database_pool_size
        }
    }
