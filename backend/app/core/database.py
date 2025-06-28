"""
Database configuration and session management with optimizations.
"""
import time
import logging
from typing import Generator
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.core.config import settings

logger = logging.getLogger(__name__)

# Database engine with optimized configuration
engine = None
SessionLocal = None


def create_optimized_engine():
    """Create database engine with optimized settings for performance and reliability."""
    global engine
    
    if engine is not None:
        return engine
    
    logger.info("Creating optimized database engine...")
    
    engine = create_engine(
        settings.database_url,
        # Connection pool settings for better resource management
        poolclass=QueuePool,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=settings.database_pool_pre_ping,
        pool_recycle=settings.database_pool_recycle,
        echo=settings.database_echo,
        
        # Performance optimizations
        connect_args={
            "connect_timeout": 10,
            "application_name": "splitwise_backend",
        }
    )
    
    # Add connection event listeners for monitoring
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logger.debug("Database connection established")
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug("Connection checked out from pool")
    
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        logger.debug("Connection checked back into pool")
    
    return engine


def create_session_factory():
    """Create session factory with proper configuration."""
    global SessionLocal
    
    if SessionLocal is not None:
        return SessionLocal
    
    if engine is None:
        create_optimized_engine()
    
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False  # Prevent lazy loading issues
    )
    
    return SessionLocal


def init_database_with_retry() -> bool:
    """Initialize database connection with retry logic."""
    max_retries = settings.db_max_retries
    retry_delay = settings.db_retry_delay
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting database connection (attempt {attempt + 1}/{max_retries})")
            
            # Create engine and test connection
            engine = create_optimized_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create session factory
            create_session_factory()
            
            logger.info(f"Database connection successful on attempt {attempt + 1}")
            
            # Import and create tables
            from app.models import Base
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            
            return True
            
        except Exception as e:
            logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                return False
    
    return False


def get_database_session() -> Generator[Session, None, None]:
    """
    Dependency to get database session with proper resource management.
    
    Yields:
        Database session that will be automatically closed after use.
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database_with_retry() first.")
    
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def get_database_health() -> dict:
    """Check database health and return status information."""
    try:
        if engine is None:
            return {
                "status": "unhealthy",
                "database": "not_initialized",
                "message": "Database engine not created"
            }
        
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as health_check"))
            result.fetchone()
        
        # Get pool information
        pool = engine.pool
        pool_status = {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow()
            # Note: 'invalid' method was removed in newer SQLAlchemy versions
        }
        
        return {
            "status": "healthy",
            "database": "connected",
            "pool_status": pool_status
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": f"error: {str(e)}"
        }


def close_database_connections():
    """Close all database connections and clean up resources."""
    global engine, SessionLocal
    
    if engine:
        logger.info("Closing database connections...")
        engine.dispose()
        engine = None
    
    if SessionLocal:
        SessionLocal = None
    
    logger.info("Database connections closed")
