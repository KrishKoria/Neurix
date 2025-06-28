"""
User-related API routes.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.users import UserService
from app.schemas.users import UserCreate, UserUpdate, UserResponse
from app.schemas.balances import UserBalanceResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/users", tags=["users"])
user_service = UserService()


@router.post("/", response_model=UserResponse, summary="Create a new user")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user with unique email validation.
    
    - **name**: User's full name (required)
    - **email**: User's email address (required, must be unique)
    """
    return user_service.create_user(db, user_data)


@router.get("/", response_model=List[UserResponse], summary="Get all users")
def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search users by name"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all users with optional pagination and search.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    - **search**: Optional search term to filter users by name
    """
    return user_service.get_users(db, skip=skip, limit=limit, search=search)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific user by their ID.
    
    - **user_id**: The ID of the user to retrieve
    """
    return user_service.get_user(db, user_id)


@router.put("/{user_id}", response_model=UserResponse, summary="Update user information")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user information.
    
    - **user_id**: The ID of the user to update
    - **name**: New name (optional)
    - **email**: New email address (optional, must be unique)
    """
    return user_service.update_user(db, user_id, user_data)


@router.delete("/{user_id}", response_model=MessageResponse, summary="Delete user")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a user. User must have no outstanding balances.
    
    - **user_id**: The ID of the user to delete
    """
    result = user_service.delete_user(db, user_id)
    return MessageResponse(message=result["message"])


@router.get("/{user_id}/balances", response_model=List[UserBalanceResponse], summary="Get user balances")
def get_user_balances(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user's balances across all groups.
    
    - **user_id**: The ID of the user
    
    Returns balance information for each group the user belongs to.
    Positive balance means the user is owed money, negative means they owe money.
    """
    return user_service.get_user_balances(db, user_id)


@router.get("/{user_id}/summary", summary="Get user summary")
def get_user_summary(
    user_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive summary for a user including groups and balance information.
    
    - **user_id**: The ID of the user
    """
    return user_service.get_user_summary(db, user_id)
