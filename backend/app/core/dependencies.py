"""
Dependency injection and utility functions.
"""
import logging
from typing import Generator, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_database_session, get_database_health
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.
    
    Yields:
        Database session with automatic cleanup.
        
    Raises:
        HTTPException: If database is not available.
    """
    try:
        db_session = next(get_database_session())
        yield db_session
    except RuntimeError as e:
        logger.error(f"Database dependency error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


def get_settings():
    """FastAPI dependency to get application settings."""
    return settings


def health_check_dependency():
    """FastAPI dependency for health check endpoint."""
    return get_database_health()


class CacheManager:
    """Simple in-memory cache manager for optimization."""
    
    def __init__(self):
        self._cache = {}
        self._ttl = {}
    
    def get(self, key: str) -> Optional[any]:
        """Get value from cache if not expired."""
        import time
        
        if key not in self._cache:
            return None
        
        if key in self._ttl and time.time() > self._ttl[key]:
            del self._cache[key]
            del self._ttl[key]
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        import time
        
        self._cache[key] = value
        if ttl:
            self._ttl[key] = time.time() + ttl
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._ttl:
            del self._ttl[key]
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._ttl.clear()


# Global cache instance
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """FastAPI dependency to get cache manager."""
    return cache_manager
