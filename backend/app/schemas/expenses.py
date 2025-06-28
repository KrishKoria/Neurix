"""
Expense-related Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal
from datetime import datetime
from decimal import Decimal


class ExpenseSplitInput(BaseModel):
    """Schema for expense split input in percentage-based splits."""
    user_id: int
    percentage: float
    
    @field_validator('percentage')
    @classmethod
    def validate_percentage(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Percentage must be between 0 and 100')
        return round(v, 2)


class ExpenseBase(BaseModel):
    """Base expense schema with common fields."""
    description: str
    amount: float
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return round(v, 2)


class ExpenseCreate(ExpenseBase):
    """Schema for creating a new expense."""
    paid_by: int
    split_type: Literal["equal", "percentage"]
    splits: Optional[List[ExpenseSplitInput]] = None
    
    @field_validator('splits')
    @classmethod
    def validate_splits(cls, v, values):
        if 'split_type' in values and values['split_type'] == 'percentage':
            if not v:
                raise ValueError('Splits must be provided for percentage split type')
            
            # Check that percentages sum to 100
            total_percentage = sum(split.percentage for split in v)
            if abs(total_percentage - 100) > 0.01:
                raise ValueError(f'Percentages must sum to 100, got {total_percentage}')
            
            # Check for duplicate user IDs
            user_ids = [split.user_id for split in v]
            if len(set(user_ids)) != len(user_ids):
                raise ValueError('Duplicate user IDs in splits')
        
        elif 'split_type' in values and values['split_type'] == 'equal':
            if v is not None:
                raise ValueError('Splits should not be provided for equal split type')
        
        return v


class ExpenseUpdate(BaseModel):
    """Schema for updating expense information."""
    description: Optional[str] = None
    amount: Optional[float] = None
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Description cannot be empty')
            return v.strip()
        return v
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Amount must be greater than 0')
            return round(v, 2)
        return v


class ExpenseSplitResponse(BaseModel):
    """Schema for expense split responses."""
    user_id: int
    user_name: str
    amount: float
    percentage: Optional[float] = None
    
    class Config:
        from_attributes = True


class ExpenseResponse(ExpenseBase):
    """Schema for expense responses with full details."""
    id: int
    group_id: int
    paid_by: int
    paid_by_name: str
    split_type: str
    splits: List[ExpenseSplitResponse]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExpenseSummary(BaseModel):
    """Lightweight expense schema for lists."""
    id: int
    description: str
    amount: float
    paid_by_name: str
    split_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True
