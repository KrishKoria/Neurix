"""
Common schemas used across the application.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class HealthResponse(BaseModel):
    """Schema for health check responses."""
    status: str
    database: str
    message: Optional[str] = None
    pool_status: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    
    class Config:
        from_attributes = True
