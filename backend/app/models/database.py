"""
Database models for the Splitwise application with optimizations.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

# Association table for many-to-many relationship between users and groups
user_group_association = Table(
    'user_groups',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    # Add indexes for performance
    Index('idx_user_groups_user_id', 'user_id'),
    Index('idx_user_groups_group_id', 'group_id'),
)


class SplitType(enum.Enum):
    EQUAL = "equal"
    PERCENTAGE = "percentage"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # Index for search
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships with optimized lazy loading
    groups = relationship(
        "Group", 
        secondary=user_group_association, 
        back_populates="users",
        lazy="select"  # Optimize for when we need user's groups
    )
    paid_expenses = relationship(
        "Expense", 
        back_populates="paid_by_user",
        lazy="select"
    )
    expense_splits = relationship(
        "ExpenseSplit", 
        back_populates="user",
        lazy="select"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"


class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # Index for search
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships with optimized lazy loading
    users = relationship(
        "User", 
        secondary=user_group_association, 
        back_populates="groups",
        lazy="select"
    )
    expenses = relationship(
        "Expense", 
        back_populates="group",
        lazy="select",
        order_by="desc(Expense.created_at)"  # Always get expenses in descending order
    )
    
    def __repr__(self):
        return f"<Group(id={self.id}, name='{self.name}')>"


class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False, index=True)  # Index for sorting by amount
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    paid_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    split_type = Column(Enum(SplitType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    group = relationship("Group", back_populates="expenses")
    paid_by_user = relationship("User", back_populates="paid_expenses")
    splits = relationship(
        "ExpenseSplit", 
        back_populates="expense", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_expenses_group_created', 'group_id', 'created_at'),
        Index('idx_expenses_paid_by_group', 'paid_by', 'group_id'),
        Index('idx_expenses_group_amount', 'group_id', 'amount'),
    )
    
    def __repr__(self):
        return f"<Expense(id={self.id}, description='{self.description}', amount={self.amount})>"


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False, index=True)  # Amount this user owes for this expense
    percentage = Column(Float, nullable=True)  # Only used for percentage splits
    
    # Relationships
    expense = relationship("Expense", back_populates="splits")
    user = relationship("User", back_populates="expense_splits")
    
    # Composite indexes for balance calculations
    __table_args__ = (
        Index('idx_expense_splits_user_expense', 'user_id', 'expense_id'),
        Index('idx_expense_splits_expense_user', 'expense_id', 'user_id'),
    )
    
    def __repr__(self):
        return f"<ExpenseSplit(id={self.id}, user_id={self.user_id}, amount={self.amount})>"
