"""
Group-related API routes.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.groups import GroupService
from app.schemas.groups import GroupCreate, GroupUpdate, GroupResponse, GroupSummary
from app.schemas.balances import BalanceResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/groups", tags=["groups"])
group_service = GroupService()


@router.post("/", response_model=GroupResponse, summary="Create a new group")
def create_group(
    group_data: GroupCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new group with specified users.
    
    - **name**: Group name (required)
    - **user_ids**: List of user IDs to add to the group (minimum 2 users)
    """
    return group_service.create_group(db, group_data)


@router.get("/", response_model=List[GroupSummary], summary="Get all groups")
def get_groups(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search groups by name"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all groups with optional pagination and search.
    
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-1000)
    - **search**: Optional search term to filter groups by name
    """
    return group_service.get_groups(db, skip=skip, limit=limit, search=search)


@router.get("/{group_id}", response_model=GroupResponse, summary="Get group by ID")
def get_group(
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific group by its ID with full details.
    
    - **group_id**: The ID of the group to retrieve
    """
    return group_service.get_group(db, group_id)


@router.put("/{group_id}", response_model=GroupResponse, summary="Update group information")
def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: Session = Depends(get_db)
):
    """
    Update group information including name and members.
    
    - **group_id**: The ID of the group to update
    - **name**: New group name (optional)
    - **user_ids**: New list of user IDs (optional, minimum 2 users)
    """
    return group_service.update_group(db, group_id, group_data)


@router.delete("/{group_id}", response_model=MessageResponse, summary="Delete group")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a group. Group must have no expenses.
    
    - **group_id**: The ID of the group to delete
    """
    result = group_service.delete_group(db, group_id)
    return MessageResponse(message=result["message"])


@router.get("/{group_id}/balances", response_model=List[BalanceResponse], summary="Get group balances")
def get_group_balances(
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Get balance information for all users in a group.
    
    - **group_id**: The ID of the group
    
    Returns balance information for each user in the group.
    Positive balance means the user is owed money, negative means they owe money.
    """
    return group_service.get_group_balances(db, group_id)


@router.get("/{group_id}/settlements", summary="Get settlement suggestions")
def get_settlement_suggestions(
    group_id: int,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get settlement suggestions to minimize the number of transactions needed to settle all balances.
    
    - **group_id**: The ID of the group
    
    Returns a list of suggested transactions to settle all balances.
    """
    return group_service.get_settlement_suggestions(db, group_id)
