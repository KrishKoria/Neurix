"""
Group repository with optimized database operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, func, desc
from app.models.database import Group, User, Expense, ExpenseSplit
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository):
    """Repository for Group model with optimized queries."""
    
    def __init__(self):
        super().__init__(Group)
    
    def get_with_users(self, db: Session, group_id: int) -> Optional[Group]:
        """Get group with users (optimized with eager loading)."""
        return (
            db.query(Group)
            .options(joinedload(Group.users))
            .filter(Group.id == group_id)
            .first()
        )
    
    def get_with_expenses(self, db: Session, group_id: int, limit: int = 50) -> Optional[Group]:
        """Get group with recent expenses (optimized)."""
        return (
            db.query(Group)
            .options(
                joinedload(Group.users),
                selectinload(Group.expenses).joinedload(Expense.paid_by_user),
                selectinload(Group.expenses).joinedload(Expense.splits)
            )
            .filter(Group.id == group_id)
            .first()
        )
    
    def get_full_context(self, db: Session, group_id: int) -> Optional[Group]:
        """Get group with all related data for comprehensive operations."""
        return (
            db.query(Group)
            .options(
                joinedload(Group.users),
                selectinload(Group.expenses).joinedload(Expense.paid_by_user),
                selectinload(Group.expenses).joinedload(Expense.splits).joinedload(ExpenseSplit.user)
            )
            .filter(Group.id == group_id)
            .first()
        )
    
    def get_groups_for_user(self, db: Session, user_id: int) -> List[Group]:
        """Get all groups for a specific user."""
        return (
            db.query(Group)
            .join(Group.users)
            .filter(User.id == user_id)
            .order_by(Group.name)
            .all()
        )
    
    def get_group_summary(self, db: Session, group_id: int) -> Optional[Dict[str, Any]]:
        """Get group summary with calculated totals."""
        group = (
            db.query(Group)
            .options(joinedload(Group.users))
            .filter(Group.id == group_id)
            .first()
        )
        
        if not group:
            return None
        
        # Calculate total expenses
        total_expenses = (
            db.query(func.sum(Expense.amount))
            .filter(Expense.group_id == group_id)
            .scalar() or 0
        )
        
        # Count expenses
        expense_count = (
            db.query(func.count(Expense.id))
            .filter(Expense.group_id == group_id)
            .scalar() or 0
        )
        
        return {
            "id": group.id,
            "name": group.name,
            "member_count": len(group.users),
            "total_expenses": float(total_expenses),
            "expense_count": expense_count,
            "created_at": group.created_at
        }
    
    def search_by_name(self, db: Session, name: str, limit: int = 10) -> List[Group]:
        """Search groups by name (case-insensitive)."""
        return (
            db.query(Group)
            .filter(Group.name.ilike(f"%{name}%"))
            .order_by(Group.name)
            .limit(limit)
            .all()
        )
    
    def get_recent_groups(self, db: Session, limit: int = 10) -> List[Group]:
        """Get recently created groups."""
        return (
            db.query(Group)
            .options(joinedload(Group.users))
            .order_by(desc(Group.created_at))
            .limit(limit)
            .all()
        )
    
    def check_user_in_group(self, db: Session, group_id: int, user_id: int) -> bool:
        """Check if a user is a member of a group."""
        return (
            db.query(Group)
            .join(Group.users)
            .filter(and_(Group.id == group_id, User.id == user_id))
            .first() is not None
        )
    
    def get_groups_with_balances(self, db: Session, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get groups with their balance summaries."""
        groups = (
            db.query(Group)
            .options(joinedload(Group.users))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        result = []
        for group in groups:
            total_expenses = (
                db.query(func.sum(Expense.amount))
                .filter(Expense.group_id == group.id)
                .scalar() or 0
            )
            
            result.append({
                "id": group.id,
                "name": group.name,
                "users": [{"id": u.id, "name": u.name} for u in group.users],
                "total_expenses": float(total_expenses),
                "member_count": len(group.users),
                "created_at": group.created_at
            })
        
        return result
