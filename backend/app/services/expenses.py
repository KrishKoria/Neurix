"""
Expense service with business logic and validation.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.expenses import ExpenseRepository, ExpenseSplitRepository
from app.repositories.groups import GroupRepository
from app.repositories.users import UserRepository
from app.repositories.balances import BalanceRepository
from app.schemas.expenses import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseSummary,
    ExpenseSplitResponse
)
from app.models.database import SplitType

logger = logging.getLogger(__name__)


class ExpenseService:
    """Service class for expense-related business logic."""
    
    def __init__(self):
        self.expense_repo = ExpenseRepository()
        self.split_repo = ExpenseSplitRepository()
        self.group_repo = GroupRepository()
        self.user_repo = UserRepository()
        self.balance_repo = BalanceRepository()
    
    def create_expense(self, db: Session, group_id: int, expense_data: ExpenseCreate) -> ExpenseResponse:
        """Create a new expense with splits."""
        try:
            # Verify group exists
            group = self.group_repo.get_with_users(db, group_id)
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail="Group not found"
                )
            
            # Verify paid_by user is in the group
            group_user_ids = [user.id for user in group.users]
            if expense_data.paid_by not in group_user_ids:
                raise HTTPException(
                    status_code=400,
                    detail="User who paid is not in the group"
                )
            
            # Prepare expense data
            expense_dict = {
                "description": expense_data.description,
                "amount": expense_data.amount,
                "group_id": group_id,
                "paid_by": expense_data.paid_by,
                "split_type": SplitType(expense_data.split_type)
            }
            
            # Prepare splits data
            splits_data = []
            
            if expense_data.split_type == "equal":
                # Equal split among all group members
                split_amount = expense_data.amount / len(group.users)
                for user in group.users:
                    splits_data.append({
                        "user_id": user.id,
                        "amount": split_amount
                    })
            
            elif expense_data.split_type == "percentage":
                # Percentage-based split
                if not expense_data.splits:
                    raise HTTPException(
                        status_code=400,
                        detail="Splits must be provided for percentage split type"
                    )
                
                for split_input in expense_data.splits:
                    # Verify user is in group
                    if split_input.user_id not in group_user_ids:
                        raise HTTPException(
                            status_code=400,
                            detail=f"User {split_input.user_id} is not in the group"
                        )
                    
                    split_amount = (split_input.percentage / 100) * expense_data.amount
                    splits_data.append({
                        "user_id": split_input.user_id,
                        "amount": split_amount,
                        "percentage": split_input.percentage
                    })
            
            # Create expense with splits
            expense = self.expense_repo.create_expense_with_splits(
                db, expense_dict, splits_data
            )
            
            # Invalidate balance caches
            for user in group.users:
                self.balance_repo.invalidate_balance_cache(user.id, group_id)
            
            logger.info(f"Created expense: {expense.description} for group {group_id}")
            
            # Convert to response format
            return self._expense_to_response(expense)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating expense: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create expense"
            )
    
    def get_expense(self, db: Session, expense_id: int) -> ExpenseResponse:
        """Get expense by ID with all details."""
        try:
            expense = self.expense_repo.get_with_splits(db, expense_id)
            if not expense:
                raise HTTPException(
                    status_code=404,
                    detail="Expense not found"
                )
            
            return self._expense_to_response(expense)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting expense {expense_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve expense"
            )
    
    def get_group_expenses(
        self,
        db: Session,
        group_id: int,
        skip: int = 0,
        limit: int = 50,
        order_by: str = "created_at"
    ) -> List[ExpenseSummary]:
        """Get expenses for a group."""
        try:
            # Verify group exists
            group = self.group_repo.get(db, group_id)
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail="Group not found"
                )
            
            expenses = self.expense_repo.get_group_expenses(
                db, group_id, skip, limit, order_by, desc_order=True
            )
            
            return [
                ExpenseSummary(
                    id=expense.id,
                    description=expense.description,
                    amount=expense.amount,
                    paid_by_name=expense.paid_by_user.name,
                    split_type=expense.split_type.value,
                    created_at=expense.created_at
                )
                for expense in expenses
            ]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting group expenses for {group_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve group expenses"
            )
    
    def update_expense(self, db: Session, expense_id: int, expense_data: ExpenseUpdate) -> ExpenseResponse:
        """Update expense information (limited updates)."""
        try:
            expense = self.expense_repo.get_with_splits(db, expense_id)
            if not expense:
                raise HTTPException(
                    status_code=404,
                    detail="Expense not found"
                )
            
            # Only allow updating description and amount
            update_data = expense_data.dict(exclude_unset=True)
            
            if update_data:
                updated_expense = self.expense_repo.update(
                    db, db_obj=expense, obj_in=update_data
                )
                
                # If amount was updated, recalculate splits for equal split type
                if "amount" in update_data and expense.split_type == SplitType.EQUAL:
                    # Update split amounts
                    for split in expense.splits:
                        new_amount = updated_expense.amount / len(expense.splits)
                        self.split_repo.update(
                            db, db_obj=split, obj_in={"amount": new_amount}
                        )
                
                # Invalidate caches
                group_users = self.user_repo.get_users_in_group(db, expense.group_id)
                for user in group_users:
                    self.balance_repo.invalidate_balance_cache(user.id, expense.group_id)
                
                # Refresh expense
                updated_expense = self.expense_repo.get_with_splits(db, expense_id)
                
                logger.info(f"Updated expense: {updated_expense.description}")
                return self._expense_to_response(updated_expense)
            
            return self._expense_to_response(expense)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating expense {expense_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to update expense"
            )
    
    def delete_expense(self, db: Session, expense_id: int) -> Dict[str, str]:
        """Delete expense and its splits."""
        try:
            expense = self.expense_repo.get_with_splits(db, expense_id)
            if not expense:
                raise HTTPException(
                    status_code=404,
                    detail="Expense not found"
                )
            
            group_id = expense.group_id
            
            # Get affected users for cache invalidation
            group_users = self.user_repo.get_users_in_group(db, group_id)
            
            # Remove expense (splits will be cascade deleted)
            self.expense_repo.remove(db, id=expense_id)
            
            # Invalidate caches
            for user in group_users:
                self.balance_repo.invalidate_balance_cache(user.id, group_id)
            
            logger.info(f"Deleted expense: {expense.description}")
            return {"message": "Expense deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting expense {expense_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete expense"
            )
    
    def get_expense_statistics(self, db: Session, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get expense statistics."""
        try:
            if group_id:
                # Verify group exists
                group = self.group_repo.get(db, group_id)
                if not group:
                    raise HTTPException(
                        status_code=404,
                        detail="Group not found"
                    )
            
            stats = self.expense_repo.get_expense_statistics(db, group_id)
            return stats
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting expense statistics: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve expense statistics"
            )
    
    def _expense_to_response(self, expense) -> ExpenseResponse:
        """Convert expense model to response schema."""
        splits = [
            ExpenseSplitResponse(
                user_id=split.user_id,
                user_name=split.user.name,
                amount=split.amount,
                percentage=split.percentage
            )
            for split in expense.splits
        ]
        
        return ExpenseResponse(
            id=expense.id,
            description=expense.description,
            amount=expense.amount,
            group_id=expense.group_id,
            paid_by=expense.paid_by,
            paid_by_name=expense.paid_by_user.name,
            split_type=expense.split_type.value,
            splits=splits,
            created_at=expense.created_at
        )
