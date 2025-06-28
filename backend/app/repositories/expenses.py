"""
Expense repository with optimized database operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, func, desc, asc
from datetime import datetime, timedelta
from app.models.database import Expense, ExpenseSplit, User, Group
from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository):
    """Repository for Expense model with optimized queries."""
    
    def __init__(self):
        super().__init__(Expense)
    
    def get_with_splits(self, db: Session, expense_id: int) -> Optional[Expense]:
        """Get expense with all splits and user information."""
        return (
            db.query(Expense)
            .options(
                joinedload(Expense.paid_by_user),
                joinedload(Expense.group),
                selectinload(Expense.splits).joinedload(ExpenseSplit.user)
            )
            .filter(Expense.id == expense_id)
            .first()
        )
    
    def get_group_expenses(
        self, 
        db: Session, 
        group_id: int, 
        skip: int = 0, 
        limit: int = 50,
        order_by: str = "created_at",
        desc_order: bool = True
    ) -> List[Expense]:
        """Get expenses for a group with pagination and ordering."""
        query = (
            db.query(Expense)
            .options(
                joinedload(Expense.paid_by_user),
                selectinload(Expense.splits).joinedload(ExpenseSplit.user)
            )
            .filter(Expense.group_id == group_id)
        )
        
        # Apply ordering
        if hasattr(Expense, order_by):
            order_field = getattr(Expense, order_by)
            if desc_order:
                query = query.order_by(desc(order_field))
            else:
                query = query.order_by(asc(order_field))
        
        return query.offset(skip).limit(limit).all()
    
    def get_user_expenses(
        self, 
        db: Session, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Expense]:
        """Get expenses paid by a specific user."""
        return (
            db.query(Expense)
            .options(
                joinedload(Expense.group),
                selectinload(Expense.splits).joinedload(ExpenseSplit.user)
            )
            .filter(Expense.paid_by == user_id)
            .order_by(desc(Expense.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_recent_expenses(
        self, 
        db: Session, 
        days: int = 7, 
        limit: int = 20
    ) -> List[Expense]:
        """Get recent expenses across all groups."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return (
            db.query(Expense)
            .options(
                joinedload(Expense.paid_by_user),
                joinedload(Expense.group)
            )
            .filter(Expense.created_at >= cutoff_date)
            .order_by(desc(Expense.created_at))
            .limit(limit)
            .all()
        )
    
    def get_expenses_by_amount_range(
        self, 
        db: Session, 
        min_amount: float, 
        max_amount: float,
        group_id: Optional[int] = None
    ) -> List[Expense]:
        """Get expenses within a specific amount range."""
        query = (
            db.query(Expense)
            .options(
                joinedload(Expense.paid_by_user),
                joinedload(Expense.group)
            )
            .filter(and_(
                Expense.amount >= min_amount,
                Expense.amount <= max_amount
            ))
        )
        
        if group_id:
            query = query.filter(Expense.group_id == group_id)
        
        return query.order_by(desc(Expense.amount)).all()
    
    def get_expense_statistics(self, db: Session, group_id: Optional[int] = None) -> Dict[str, Any]:
        """Get expense statistics for a group or overall."""
        query = db.query(Expense)
        
        if group_id:
            query = query.filter(Expense.group_id == group_id)
        
        stats = query.with_entities(
            func.count(Expense.id).label('total_expenses'),
            func.sum(Expense.amount).label('total_amount'),
            func.avg(Expense.amount).label('avg_amount'),
            func.min(Expense.amount).label('min_amount'),
            func.max(Expense.amount).label('max_amount')
        ).first()
        
        return {
            "total_expenses": stats.total_expenses or 0,
            "total_amount": float(stats.total_amount or 0),
            "average_amount": float(stats.avg_amount or 0),
            "minimum_amount": float(stats.min_amount or 0),
            "maximum_amount": float(stats.max_amount or 0)
        }
    
    def create_expense_with_splits(
        self, 
        db: Session, 
        expense_data: Dict[str, Any],
        splits_data: List[Dict[str, Any]]
    ) -> Expense:
        """Create expense with splits in a single transaction."""
        try:
            # Create expense
            expense = Expense(**expense_data)
            db.add(expense)
            db.flush()  # Get the expense ID
            
            # Create splits
            for split_data in splits_data:
                split = ExpenseSplit(
                    expense_id=expense.id,
                    **split_data
                )
                db.add(split)
            
            db.commit()
            db.refresh(expense)
            
            # Load related data
            return self.get_with_splits(db, expense.id)
            
        except Exception as e:
            db.rollback()
            raise e


class ExpenseSplitRepository(BaseRepository):
    """Repository for ExpenseSplit model with optimized queries."""
    
    def __init__(self):
        super().__init__(ExpenseSplit)
    
    def get_user_splits_in_group(
        self, 
        db: Session, 
        user_id: int, 
        group_id: int
    ) -> List[ExpenseSplit]:
        """Get all expense splits for a user in a specific group."""
        return (
            db.query(ExpenseSplit)
            .join(Expense)
            .options(joinedload(ExpenseSplit.expense))
            .filter(and_(
                ExpenseSplit.user_id == user_id,
                Expense.group_id == group_id
            ))
            .order_by(desc(Expense.created_at))
            .all()
        )
    
    def get_splits_by_expense(self, db: Session, expense_id: int) -> List[ExpenseSplit]:
        """Get all splits for a specific expense."""
        return (
            db.query(ExpenseSplit)
            .options(joinedload(ExpenseSplit.user))
            .filter(ExpenseSplit.expense_id == expense_id)
            .order_by(ExpenseSplit.amount.desc())
            .all()
        )
