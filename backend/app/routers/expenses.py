"""
Expense-related API routes.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.expenses import ExpenseService
from app.schemas.expenses import ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseSummary
from app.schemas.common import MessageResponse

router = APIRouter(tags=["expenses"])
expense_service = ExpenseService()


@router.post("/groups/{group_id}/expenses", response_model=ExpenseResponse, summary="Create a new expense")
def create_expense(
    group_id: int = Path(..., description="The ID of the group"),
    expense_data: ExpenseCreate = ...,
    db: Session = Depends(get_db)
):
    """
    Add a new expense to a group.
    
    - **group_id**: The ID of the group to add the expense to
    - **description**: Description of the expense
    - **amount**: Total amount of the expense
    - **paid_by**: ID of the user who paid for the expense
    - **split_type**: Either "equal" or "percentage"
    - **splits**: Required for percentage splits, specifying user_id and percentage for each user
    
    For equal splits, the amount is divided equally among all group members.
    For percentage splits, you must specify the percentage for each user (must sum to 100%).
    """
    return expense_service.create_expense(db, group_id, expense_data)


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse, summary="Get expense by ID")
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific expense by its ID with all split details.
    
    - **expense_id**: The ID of the expense to retrieve
    """
    return expense_service.get_expense(db, expense_id)


@router.get("/groups/{group_id}/expenses", response_model=List[ExpenseSummary], summary="Get group expenses")
def get_group_expenses(
    group_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records to return"),
    order_by: str = Query("created_at", description="Field to order by"),
    db: Session = Depends(get_db)
):
    """
    Get expenses for a specific group with pagination.
    
    - **group_id**: The ID of the group
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-200)
    - **order_by**: Field to order by (created_at, amount, description)
    
    Returns expenses in descending order by the specified field.
    """
    return expense_service.get_group_expenses(db, group_id, skip, limit, order_by)


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse, summary="Update expense")
def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db)
):
    """
    Update expense information (limited to description and amount).
    
    - **expense_id**: The ID of the expense to update
    - **description**: New description (optional)
    - **amount**: New amount (optional, will recalculate equal splits)
    
    Note: Changing the amount for equal splits will automatically recalculate all split amounts.
    Percentage splits cannot be modified after creation.
    """
    return expense_service.update_expense(db, expense_id, expense_data)


@router.delete("/expenses/{expense_id}", response_model=MessageResponse, summary="Delete expense")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an expense and all its associated splits.
    
    - **expense_id**: The ID of the expense to delete
    """
    result = expense_service.delete_expense(db, expense_id)
    return MessageResponse(message=result["message"])


@router.get("/expenses/statistics", summary="Get expense statistics")
def get_expense_statistics(
    group_id: Optional[int] = Query(None, description="Group ID for group-specific statistics"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get expense statistics for a group or system-wide.
    
    - **group_id**: Optional group ID. If not provided, returns system-wide statistics.
    
    Returns statistics including total expenses, total amount, averages, min/max amounts.
    """
    return expense_service.get_expense_statistics(db, group_id)
