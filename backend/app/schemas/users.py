"""
User-related Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields."""
    name: str
    email: EmailStr
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Name cannot be empty')
            if len(v.strip()) < 2:
                raise ValueError('Name must be at least 2 characters long')
            return v.strip()
        return v


class UserResponse(UserBase):
    """Schema for user responses."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    """Lightweight user schema for lists and references."""
    id: int
    name: str
    
    class Config:
        from_attributes = True
