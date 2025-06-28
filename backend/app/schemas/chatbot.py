"""
Chatbot-related Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional


class ChatbotQuery(BaseModel):
    """Schema for chatbot query requests."""
    query: str
    user_context: Optional[Dict[str, Any]] = None
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        if len(v.strip()) > 1000:
            raise ValueError('Query too long (max 1000 characters)')
        return v.strip()


class ChatbotResponse(BaseModel):
    """Schema for chatbot responses."""
    response: str
    context_used: Optional[Dict[str, Any]] = None
    cached: bool = False
    response_time_ms: Optional[float] = None
    
    class Config:
        from_attributes = True
