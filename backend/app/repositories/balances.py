"""
Balance repository with optimized balance calculations.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.database import User, Group, Expense, ExpenseSplit
from app.core.dependencies import cache_manager
from app.core.config import settings


class BalanceRepository:
    """Repository for balance calculations with caching and optimizations."""
    
    def __init__(self):
        self.cache = cache_manager
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key for balance calculations."""
        return f"{prefix}:{'_'.join(map(str, args))}"
    
    def get_user_balance_in_group(self, db: Session, user_id: int, group_id: int) -> Dict[str, Any]:
        """Get balance for a specific user in a specific group."""
        cache_key = self._get_cache_key("user_group_balance", user_id, group_id)
        cached = self.cache.get(cache_key)
        
        if cached:
            return cached
        
        # Amount user paid for group expenses
        paid_amount = (
            db.query(func.coalesce(func.sum(Expense.amount), 0))
            .filter(and_(Expense.group_id == group_id, Expense.paid_by == user_id))
            .scalar()
        )
        
        # Amount user owes from expense splits
        owed_amount = (
            db.query(func.coalesce(func.sum(ExpenseSplit.amount), 0))
            .join(Expense)
            .filter(and_(Expense.group_id == group_id, ExpenseSplit.user_id == user_id))
            .scalar()
        )
        
        balance = float(paid_amount - owed_amount)
        
        result = {
            "user_id": user_id,
            "group_id": group_id,
            "balance": balance,
            "paid_total": float(paid_amount),
            "owes_total": float(owed_amount)
        }
        
        # Cache for 1 minute
        self.cache.set(cache_key, result, ttl=settings.balance_cache_ttl)
        return result
    
    def get_group_balances(self, db: Session, group_id: int) -> List[Dict[str, Any]]:
        """Get balances for all users in a group."""
        cache_key = self._get_cache_key("group_balances", group_id)
        cached = self.cache.get(cache_key)
        
        if cached:
            return cached
        
        # Get all users in the group
        group = (
            db.query(Group)
            .filter(Group.id == group_id)
            .first()
        )
        
        if not group:
            return []
        
        balances = []
        for user in group.users:
            balance_data = self.get_user_balance_in_group(db, user.id, group_id)
            balance_data["user_name"] = user.name
            balances.append(balance_data)
        
        # Sort by balance (highest debt first, then highest credit)
        balances.sort(key=lambda x: x["balance"])
        
        # Cache for 1 minute
        self.cache.set(cache_key, balances, ttl=settings.balance_cache_ttl)
        return balances
    
    def get_user_all_balances(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Get balances for a user across all their groups."""
        cache_key = self._get_cache_key("user_all_balances", user_id)
        cached = self.cache.get(cache_key)
        
        if cached:
            return cached
        
        # Get all groups for the user
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )
        
        if not user:
            return []
        
        balances = []
        for group in user.groups:
            balance_data = self.get_user_balance_in_group(db, user_id, group.id)
            balance_data["group_name"] = group.name
            balances.append(balance_data)
        
        # Sort by group name
        balances.sort(key=lambda x: x["group_name"])
        
        # Cache for 1 minute
        self.cache.set(cache_key, balances, ttl=settings.balance_cache_ttl)
        return balances
    
    def get_balance_summary(self, db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get balance summary for a user or overall system."""
        cache_key = self._get_cache_key("balance_summary", user_id or "system")
        cached = self.cache.get(cache_key)
        
        if cached:
            return cached
        
        if user_id:
            # User-specific summary
            balances = self.get_user_all_balances(db, user_id)
            
            total_balance = sum(b["balance"] for b in balances)
            groups_with_debt = len([b for b in balances if b["balance"] < 0])
            groups_with_credit = len([b for b in balances if b["balance"] > 0])
            
            largest_debt = min((b["balance"] for b in balances if b["balance"] < 0), default=0)
            largest_credit = max((b["balance"] for b in balances if b["balance"] > 0), default=0)
            
        else:
            # System-wide summary
            total_expenses = (
                db.query(func.coalesce(func.sum(Expense.amount), 0))
                .scalar()
            )
            
            total_balance = 0  # System-wide balance should always be 0
            groups_with_debt = 0
            groups_with_credit = 0
            largest_debt = 0
            largest_credit = 0
            
            # Count groups
            total_groups = db.query(func.count(Group.id)).scalar()
            
        result = {
            "total_balance": float(total_balance),
            "groups_with_debt": groups_with_debt,
            "groups_with_credit": groups_with_credit,
            "largest_debt": float(largest_debt),
            "largest_credit": float(largest_credit)
        }
        
        # Cache for 5 minutes
        self.cache.set(cache_key, result, ttl=300)
        return result
    
    def invalidate_balance_cache(self, user_id: Optional[int] = None, group_id: Optional[int] = None):
        """Invalidate balance caches when data changes."""
        if user_id and group_id:
            # Invalidate specific user-group balance
            cache_key = self._get_cache_key("user_group_balance", user_id, group_id)
            self.cache.delete(cache_key)
        
        if group_id:
            # Invalidate group balances
            cache_key = self._get_cache_key("group_balances", group_id)
            self.cache.delete(cache_key)
        
        if user_id:
            # Invalidate user all balances
            cache_key = self._get_cache_key("user_all_balances", user_id)
            self.cache.delete(cache_key)
            
            # Invalidate user summary
            cache_key = self._get_cache_key("balance_summary", user_id)
            self.cache.delete(cache_key)
        
        # Invalidate system summary
        cache_key = self._get_cache_key("balance_summary", "system")
        self.cache.delete(cache_key)
    
    def get_settlement_suggestions(self, db: Session, group_id: int) -> List[Dict[str, Any]]:
        """Get suggestions for settling balances in a group."""
        balances = self.get_group_balances(db, group_id)
        
        # Separate debtors and creditors
        debtors = [b for b in balances if b["balance"] < 0]
        creditors = [b for b in balances if b["balance"] > 0]
        
        suggestions = []
        
        # Simple settlement algorithm: match largest debt with largest credit
        debtors.sort(key=lambda x: x["balance"])  # Most debt first
        creditors.sort(key=lambda x: x["balance"], reverse=True)  # Most credit first
        
        i, j = 0, 0
        while i < len(debtors) and j < len(creditors):
            debt = abs(debtors[i]["balance"])
            credit = creditors[j]["balance"]
            
            settlement_amount = min(debt, credit)
            
            if settlement_amount > 0.01:  # Only suggest settlements > 1 cent
                suggestions.append({
                    "from_user_id": debtors[i]["user_id"],
                    "from_user_name": debtors[i]["user_name"],
                    "to_user_id": creditors[j]["user_id"],
                    "to_user_name": creditors[j]["user_name"],
                    "amount": round(settlement_amount, 2)
                })
            
            # Update balances
            debtors[i]["balance"] += settlement_amount
            creditors[j]["balance"] -= settlement_amount
            
            # Move to next if current is settled
            if abs(debtors[i]["balance"]) < 0.01:
                i += 1
            if abs(creditors[j]["balance"]) < 0.01:
                j += 1
        
        return suggestions
