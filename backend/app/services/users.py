"""
User service with business logic and validation.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.users import UserRepository
from app.repositories.balances import BalanceRepository
from app.schemas.users import UserCreate, UserUpdate, UserResponse, UserSummary
from app.schemas.balances import UserBalanceResponse

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related business logic."""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.balance_repo = BalanceRepository()
    
    def create_user(self, db: Session, user_data: UserCreate) -> UserResponse:
        """Create a new user with validation."""
        try:
            # Check if email already exists
            existing_user = self.user_repo.get_by_email(db, user_data.email)
            if existing_user:
                logger.warning(f"Attempt to create user with existing email: {user_data.email}")
                raise HTTPException(
                    status_code=400, 
                    detail="Email already registered"
                )
            
            # Create user
            user_dict = user_data.dict()
            user = self.user_repo.create(db, obj_in=user_dict)
            
            logger.info(f"Created user: {user.name} ({user.email})")
            return UserResponse.from_orm(user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create user"
            )
    
    def get_user(self, db: Session, user_id: int) -> UserResponse:
        """Get user by ID."""
        user = self.user_repo.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        return UserResponse.from_orm(user)
    
    def get_users(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[UserResponse]:
        """Get users with optional search."""
        try:
            if search:
                users = self.user_repo.search_by_name(db, search, limit)
            else:
                users = self.user_repo.get_multi(
                    db, 
                    skip=skip, 
                    limit=limit,
                    order_by="name"
                )
            
            return [UserResponse.from_orm(user) for user in users]
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve users"
            )
    
    def update_user(self, db: Session, user_id: int, user_data: UserUpdate) -> UserResponse:
        """Update user information."""
        try:
            user = self.user_repo.get(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            # Check email uniqueness if email is being updated
            if user_data.email and user_data.email != user.email:
                if self.user_repo.check_email_exists(db, user_data.email, exclude_id=user_id):
                    raise HTTPException(
                        status_code=400,
                        detail="Email already registered"
                    )
            
            # Update user
            update_data = user_data.dict(exclude_unset=True)
            updated_user = self.user_repo.update(db, db_obj=user, obj_in=update_data)
            
            logger.info(f"Updated user: {updated_user.name}")
            return UserResponse.from_orm(updated_user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to update user"
            )
    
    def delete_user(self, db: Session, user_id: int) -> Dict[str, str]:
        """Delete user (soft delete or validation)."""
        try:
            user = self.user_repo.get(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            # Check if user has any financial obligations
            balances = self.balance_repo.get_user_all_balances(db, user_id)
            has_outstanding_balance = any(
                abs(balance["balance"]) > 0.01 for balance in balances
            )
            
            if has_outstanding_balance:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete user with outstanding balances. Please settle all debts first."
                )
            
            # Remove user
            self.user_repo.remove(db, id=user_id)
            
            # Invalidate caches
            self.balance_repo.invalidate_balance_cache(user_id=user_id)
            
            logger.info(f"Deleted user: {user.name}")
            return {"message": "User deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete user"
            )
    
    def get_user_balances(self, db: Session, user_id: int) -> List[UserBalanceResponse]:
        """Get user balances across all groups."""
        try:
            user = self.user_repo.get(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            balances = self.balance_repo.get_user_all_balances(db, user_id)
            
            return [
                UserBalanceResponse(
                    group_id=balance["group_id"],
                    group_name=balance["group_name"],
                    balance=balance["balance"],
                    paid_total=balance["paid_total"],
                    owes_total=balance["owes_total"]
                )
                for balance in balances
            ]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user balances for {user_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve user balances"
            )
    
    def get_user_summary(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user summary."""
        try:
            user = self.user_repo.get_with_groups(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            balances = self.balance_repo.get_user_all_balances(db, user_id)
            balance_summary = self.balance_repo.get_balance_summary(db, user_id)
            
            return {
                "user": UserResponse.from_orm(user),
                "groups_count": len(user.groups),
                "groups": [
                    {"id": group.id, "name": group.name} 
                    for group in user.groups
                ],
                "total_balance": balance_summary["total_balance"],
                "groups_with_debt": balance_summary["groups_with_debt"],
                "groups_with_credit": balance_summary["groups_with_credit"],
                "balances": balances
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user summary for {user_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve user summary"
            )
