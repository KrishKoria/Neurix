"""
Group service with business logic and validation.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.groups import GroupRepository
from app.repositories.users import UserRepository
from app.repositories.balances import BalanceRepository
from app.schemas.groups import GroupCreate, GroupUpdate, GroupResponse, GroupSummary
from app.schemas.balances import BalanceResponse
from app.schemas.users import UserSummary

logger = logging.getLogger(__name__)


class GroupService:
    """Service class for group-related business logic."""
    
    def __init__(self):
        self.group_repo = GroupRepository()
        self.user_repo = UserRepository()
        self.balance_repo = BalanceRepository()
    
    def create_group(self, db: Session, group_data: GroupCreate) -> GroupResponse:
        """Create a new group with validation."""
        try:
            # Verify all users exist
            users = []
            for user_id in group_data.user_ids:
                user = self.user_repo.get(db, user_id)
                if not user:
                    raise HTTPException(
                        status_code=400,
                        detail=f"User with ID {user_id} not found"
                    )
                users.append(user)
            
            # Create group
            group_dict = {"name": group_data.name}
            group = self.group_repo.create(db, obj_in=group_dict)
            
            # Add users to group
            group.users = users
            db.commit()
            db.refresh(group)
            
            logger.info(f"Created group: {group.name} with {len(users)} members")
            
            return GroupResponse(
                id=group.id,
                name=group.name,
                users=[UserSummary.from_orm(user) for user in users],
                total_expenses=0.0,
                created_at=group.created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to create group"
            )
    
    def get_group(self, db: Session, group_id: int) -> GroupResponse:
        """Get group by ID with full details."""
        try:
            group_summary = self.group_repo.get_group_summary(db, group_id)
            if not group_summary:
                raise HTTPException(
                    status_code=404,
                    detail="Group not found"
                )
            
            group = self.group_repo.get_with_users(db, group_id)
            
            return GroupResponse(
                id=group.id,
                name=group.name,
                users=[UserSummary.from_orm(user) for user in group.users],
                total_expenses=group_summary["total_expenses"],
                created_at=group.created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting group {group_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve group"
            )
    
    def get_groups(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[GroupSummary]:
        """Get groups with optional search."""
        try:
            if search:
                groups = self.group_repo.search_by_name(db, search, limit)
                result = []
                for group in groups:
                    summary = self.group_repo.get_group_summary(db, group.id)
                    result.append(GroupSummary(
                        id=group.id,
                        name=group.name,
                        member_count=summary["member_count"],
                        total_expenses=summary["total_expenses"]
                    ))
                return result
            else:
                groups_data = self.group_repo.get_groups_with_balances(db, skip, limit)
                return [
                    GroupSummary(
                        id=group["id"],
                        name=group["name"],
                        member_count=group["member_count"],
                        total_expenses=group["total_expenses"]
                    )
                    for group in groups_data
                ]
                
        except Exception as e:
            logger.error(f"Error getting groups: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve groups"
            )
    
    def update_group(self, db: Session, group_id: int, group_data: GroupUpdate) -> GroupResponse:
        """Update group information."""
        try:
            group = self.group_repo.get_with_users(db, group_id)
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail="Group not found"
                )
            
            # Update basic info
            update_data = {}
            if group_data.name is not None:
                update_data["name"] = group_data.name
            
            if update_data:
                self.group_repo.update(db, db_obj=group, obj_in=update_data)
            
            # Update users if provided
            if group_data.user_ids is not None:
                # Verify all users exist
                users = []
                for user_id in group_data.user_ids:
                    user = self.user_repo.get(db, user_id)
                    if not user:
                        raise HTTPException(
                            status_code=400,
                            detail=f"User with ID {user_id} not found"
                        )
                    users.append(user)
                
                # Update group users
                group.users = users
                db.commit()
                
                # Invalidate balance caches for this group
                self.balance_repo.invalidate_balance_cache(group_id=group_id)
            
            db.refresh(group)
            
            # Get updated summary
            summary = self.group_repo.get_group_summary(db, group_id)
            
            logger.info(f"Updated group: {group.name}")
            
            return GroupResponse(
                id=group.id,
                name=group.name,
                users=[UserSummary.from_orm(user) for user in group.users],
                total_expenses=summary["total_expenses"],
                created_at=group.created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating group {group_id}: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to update group"
            )
    
    def delete_group(self, db: Session, group_id: int) -> Dict[str, str]:
        """Delete group with validation."""
        try:
            group = self.group_repo.get(db, group_id)
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail="Group not found"
                )
            
            # Check if group has expenses
            summary = self.group_repo.get_group_summary(db, group_id)
            if summary["expense_count"] > 0:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete group with expenses. Please remove all expenses first."
                )
            
            # Remove group
            self.group_repo.remove(db, id=group_id)
            
            # Invalidate caches
            self.balance_repo.invalidate_balance_cache(group_id=group_id)
            
            logger.info(f"Deleted group: {group.name}")
            return {"message": "Group deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting group {group_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete group"
            )
    
    def get_group_balances(self, db: Session, group_id: int) -> List[BalanceResponse]:
        """Get balances for all users in a group."""
        try:
            group = self.group_repo.get(db, group_id)
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail="Group not found"
                )
            
            balances = self.balance_repo.get_group_balances(db, group_id)
            
            return [
                BalanceResponse(
                    user_id=balance["user_id"],
                    user_name=balance["user_name"],
                    balance=balance["balance"],
                    paid_total=balance["paid_total"],
                    owes_total=balance["owes_total"]
                )
                for balance in balances
            ]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting group balances for {group_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve group balances"
            )
    
    def get_settlement_suggestions(self, db: Session, group_id: int) -> List[Dict[str, Any]]:
        """Get settlement suggestions for a group."""
        try:
            group = self.group_repo.get(db, group_id)
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail="Group not found"
                )
            
            suggestions = self.balance_repo.get_settlement_suggestions(db, group_id)
            return suggestions
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting settlement suggestions for {group_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate settlement suggestions"
            )
    
    def check_user_access(self, db: Session, group_id: int, user_id: int) -> bool:
        """Check if user has access to group."""
        return self.group_repo.check_user_in_group(db, group_id, user_id)
