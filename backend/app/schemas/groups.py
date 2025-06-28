"""
Group-related Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from .users import UserResponse, UserSummary


class GroupBase(BaseModel):
    """Base group schema with common fields."""
    name: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Group name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Group name must be at least 2 characters long')
        return v.strip()


class GroupCreate(GroupBase):
    """Schema for creating a new group."""
    user_ids: List[int]
    
    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError('At least one user must be specified')
        if len(v) < 2:
            raise ValueError('A group must have at least 2 users')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate user IDs are not allowed')
        return v


class GroupUpdate(BaseModel):
    """Schema for updating group information."""
    name: Optional[str] = None
    user_ids: Optional[List[int]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Group name cannot be empty')
            if len(v.strip()) < 2:
                raise ValueError('Group name must be at least 2 characters long')
            return v.strip()
        return v
    
    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v):
        if v is not None:
            if not v:
                raise ValueError('At least one user must be specified')
            if len(v) < 2:
                raise ValueError('A group must have at least 2 users')
            if len(set(v)) != len(v):
                raise ValueError('Duplicate user IDs are not allowed')
        return v


class GroupResponse(GroupBase):
    """Schema for group responses with full details."""
    id: int
    users: List[UserSummary]
    total_expenses: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class GroupSummary(BaseModel):
    """Lightweight group schema for lists and references."""
    id: int
    name: str
    member_count: int
    total_expenses: float
    
    class Config:
        from_attributes = True
