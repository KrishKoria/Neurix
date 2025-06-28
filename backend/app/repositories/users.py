"""
User repository with optimized database operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from app.models.database import User, Group, Expense
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for User model with optimized queries."""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()
    
    def get_with_groups(self, db: Session, user_id: int) -> Optional[User]:
        """Get user with their groups (optimized with eager loading)."""
        return (
            db.query(User)
            .options(joinedload(User.groups))
            .filter(User.id == user_id)
            .first()
        )
    
    def get_with_balances(self, db: Session, user_id: int) -> Optional[User]:
        """Get user with all related data for balance calculations."""
        return (
            db.query(User)
            .options(
                joinedload(User.groups),
                joinedload(User.paid_expenses),
                joinedload(User.expense_splits)
            )
            .filter(User.id == user_id)
            .first()
        )
    
    def search_by_name(self, db: Session, name: str, limit: int = 10) -> List[User]:
        """Search users by name (case-insensitive)."""
        return (
            db.query(User)
            .filter(User.name.ilike(f"%{name}%"))
            .order_by(User.name)
            .limit(limit)
            .all()
        )
    
    def get_users_in_group(self, db: Session, group_id: int) -> List[User]:
        """Get all users in a specific group."""
        return (
            db.query(User)
            .join(User.groups)
            .filter(Group.id == group_id)
            .order_by(User.name)
            .all()
        )
    
    def get_active_users(self, db: Session, days: int = 30) -> List[User]:
        """Get users who have activity in the last N days."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return (
            db.query(User)
            .join(User.paid_expenses)
            .filter(User.paid_expenses.any(Expense.created_at >= cutoff_date))
            .distinct()
            .order_by(User.name)
            .all()
        )
    
    def check_email_exists(self, db: Session, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email already exists (useful for updates)."""
        query = db.query(User).filter(User.email == email)
        if exclude_id:
            query = query.filter(User.id != exclude_id)
        return query.first() is not None
