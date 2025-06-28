"""
Balance-related Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel
from typing import List, Optional


class BalanceResponse(BaseModel):
    """Schema for individual user balance in a group."""
    user_id: int
    user_name: str
    balance: float
    paid_total: float
    owes_total: float
    
    class Config:
        from_attributes = True


class UserBalanceResponse(BaseModel):
    """Schema for user balance across groups."""
    group_id: int
    group_name: str
    balance: float
    paid_total: float
    owes_total: float
    
    class Config:
        from_attributes = True


class BalanceSummary(BaseModel):
    """Summary of all balances for dashboard."""
    total_balance: float
    groups_with_debt: int
    groups_with_credit: int
    largest_debt: float
    largest_credit: float
    
    class Config:
        from_attributes = True
