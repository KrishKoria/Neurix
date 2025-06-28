"""
Base repository class with common database operations.
"""
from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, asc, and_, or_, func
from app.models.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations and optimizations."""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering."""
        query = db.query(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                field = order_by[1:]
                if hasattr(self.model, field):
                    query = query.order_by(desc(getattr(self.model, field)))
            else:
                if hasattr(self.model, order_by):
                    query = query.order_by(asc(getattr(self.model, order_by)))
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: Dict[str, Any]
    ) -> ModelType:
        """Update an existing record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """Remove a record by ID."""
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        query = db.query(self.model)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.count()
    
    def exists(self, db: Session, *, filters: Dict[str, Any]) -> bool:
        """Check if a record exists with given filters."""
        query = db.query(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        
        return query.first() is not None
