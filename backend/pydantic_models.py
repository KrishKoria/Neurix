from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
# Pydantic models for request/response
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True

class GroupCreate(BaseModel):
    name: str
    user_ids: List[int]

class GroupResponse(BaseModel):
    id: int
    name: str
    users: List[UserResponse]
    total_expenses: float
    
    class Config:
        from_attributes = True

class ExpenseSplitInput(BaseModel):
    user_id: int
    percentage: Optional[float] = None

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    paid_by: int
    split_type: str
    splits: Optional[List[ExpenseSplitInput]] = None
    
    @validator('split_type')
    def validate_split_type(cls, v):
        if v not in ['equal', 'percentage']:
            raise ValueError('split_type must be either "equal" or "percentage"')
        return v
    
    @validator('splits')
    def validate_splits(cls, v, values):
        if 'split_type' in values and values['split_type'] == 'percentage':
            if not v:
                raise ValueError('splits must be provided for percentage split type')
            total_percentage = sum(split.percentage or 0 for split in v)
            if abs(total_percentage - 100) > 0.01:
                raise ValueError('Percentages must sum to 100')
        return v

class BalanceResponse(BaseModel):
    user_id: int
    user_name: str
    balance: float

class UserBalanceResponse(BaseModel):
    group_id: int
    group_name: str
    balance: float

class ChatbotQuery(BaseModel):
    query: str
    user_context: Optional[Dict[str, Any]] = None

class ChatbotResponse(BaseModel):
    response: str
    context_used: Optional[Dict[str, Any]] = None
