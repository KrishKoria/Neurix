from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, validator
from typing import List, Optional, Dict
from models import Base, User, Group, Expense, ExpenseSplit, SplitType
from sqlalchemy.sql import func
import os
import time

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/splitwise")

# Retry mechanism for database connection
def create_engine_with_retry():
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(DATABASE_URL)
            # Test the connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            print(f"Database connection successful on attempt {attempt + 1}")
            return engine
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts")
                raise

engine = create_engine_with_retry()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Splitwise API", version="1.0.0", description="A simplified expense splitting application")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ...existing code... (Keep all the Pydantic models and API endpoints exactly the same)

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
    balance: float  # Positive means they are owed money, negative means they owe money

class UserBalanceResponse(BaseModel):
    group_id: int
    group_name: str
    balance: float

# API Endpoints

@app.get("/")
def root():
    return {"message": "Splitwise API is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """Get all users"""
    return db.query(User).all()

@app.post("/groups", response_model=GroupResponse)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    """Create a new group with specified users"""
    # Verify all users exist
    users = db.query(User).filter(User.id.in_(group.user_ids)).all()
    if len(users) != len(group.user_ids):
        raise HTTPException(status_code=400, detail="One or more users not found")
    
    db_group = Group(name=group.name, users=users)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    # Calculate total expenses
    total_expenses = sum(expense.amount for expense in db_group.expenses)
    
    response = GroupResponse(
        id=db_group.id,
        name=db_group.name,
        users=[UserResponse.from_orm(user) for user in db_group.users],
        total_expenses=total_expenses
    )
    return response

@app.get("/groups/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, db: Session = Depends(get_db)):
    """Get group details including users and total expenses"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    total_expenses = sum(expense.amount for expense in group.expenses)
    
    response = GroupResponse(
        id=group.id,
        name=group.name,
        users=[UserResponse.from_orm(user) for user in group.users],
        total_expenses=total_expenses
    )
    return response

@app.post("/groups/{group_id}/expenses")
def create_expense(group_id: int, expense: ExpenseCreate, db: Session = Depends(get_db)):
    """Add a new expense to a group"""
    # Verify group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify paid_by user is in the group
    if not any(user.id == expense.paid_by for user in group.users):
        raise HTTPException(status_code=400, detail="User who paid is not in the group")
    
    # Create expense
    db_expense = Expense(
        description=expense.description,
        amount=expense.amount,
        group_id=group_id,
        paid_by=expense.paid_by,
        split_type=SplitType(expense.split_type)
    )
    db.add(db_expense)
    db.flush()  # To get the expense ID
    
    # Create expense splits
    if expense.split_type == "equal":
        split_amount = expense.amount / len(group.users)
        for user in group.users:
            split = ExpenseSplit(
                expense_id=db_expense.id,
                user_id=user.id,
                amount=split_amount
            )
            db.add(split)
    else:  # percentage
        for split_input in expense.splits:
            # Verify user is in group
            if not any(user.id == split_input.user_id for user in group.users):
                raise HTTPException(status_code=400, detail=f"User {split_input.user_id} is not in the group")
            
            split_amount = (split_input.percentage / 100) * expense.amount
            split = ExpenseSplit(
                expense_id=db_expense.id,
                user_id=split_input.user_id,
                amount=split_amount,
                percentage=split_input.percentage
            )
            db.add(split)
    
    db.commit()
    return {"message": "Expense created successfully", "expense_id": db_expense.id}

@app.get("/groups/{group_id}/balances", response_model=List[BalanceResponse])
def get_group_balances(group_id: int, db: Session = Depends(get_db)):
    """Get balances for all users in a group"""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    balances = []
    
    for user in group.users:
        # Amount user paid for group expenses
        paid_amount = db.query(Expense).filter(
            and_(Expense.group_id == group_id, Expense.paid_by == user.id)
        ).with_entities(func.sum(Expense.amount)).scalar() or 0
        
        # Amount user owes from expense splits
        owed_amount = db.query(ExpenseSplit).join(Expense).filter(
            and_(Expense.group_id == group_id, ExpenseSplit.user_id == user.id)
        ).with_entities(func.sum(ExpenseSplit.amount)).scalar() or 0
        
        balance = paid_amount - owed_amount
        
        balances.append(BalanceResponse(
            user_id=user.id,
            user_name=user.name,
            balance=balance
        ))
    
    return balances

@app.get("/users/{user_id}/balances", response_model=List[UserBalanceResponse])
def get_user_balances(user_id: int, db: Session = Depends(get_db)):
    """Get balances for a user across all groups"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    balances = []
    
    for group in user.groups:
        # Amount user paid for this group's expenses
        paid_amount = db.query(Expense).filter(
            and_(Expense.group_id == group.id, Expense.paid_by == user_id)
        ).with_entities(func.sum(Expense.amount)).scalar() or 0
        
        # Amount user owes from expense splits in this group
        owed_amount = db.query(ExpenseSplit).join(Expense).filter(
            and_(Expense.group_id == group.id, ExpenseSplit.user_id == user_id)
        ).with_entities(func.sum(ExpenseSplit.amount)).scalar() or 0
        
        balance = paid_amount - owed_amount
        
        balances.append(UserBalanceResponse(
            group_id=group.id,
            group_name=group.name,
            balance=balance
        ))
    
    return balances

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)