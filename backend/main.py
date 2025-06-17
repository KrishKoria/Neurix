from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, and_, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from models import Base, User, Group, Expense, ExpenseSplit, SplitType
from sqlalchemy.sql import func
import openai
import json
import os
import time
import logging
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()  
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/splitwise")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", )
logger.info(f"Database URL: {DATABASE_URL}")
logger.info(f"DeepSeek API Key: {DEEPSEEK_API_KEY}")

# Global variables for database
engine = None
SessionLocal = None

def create_engine_with_retry():
    global engine, SessionLocal
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting database connection (attempt {attempt + 1}/{max_retries})")
            temp_engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False
            )
            
            # Test the connection
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Database connection successful on attempt {attempt + 1}")
            engine = temp_engine
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create tables
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            
            return True
        except Exception as e:
            logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                return False
    
    return False

# Initialize FastAPI app
app = FastAPI(
    title="Splitwise API", 
    version="1.0.0", 
    description="A simplified expense splitting application"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not available")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request/response
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True

class GroupCreate(BaseModel):
    name: str
    user_ids: List[int]

class GroupResponse(BaseModel):
    id: int
    name: str
    users: List[UserResponse]
    total_expenses: float
    
    class Config:
        from_attributes = True

class ExpenseSplitInput(BaseModel):
    user_id: int
    percentage: Optional[float] = None

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    paid_by: int
    split_type: str
    splits: Optional[List[ExpenseSplitInput]] = None
    
    @validator('split_type')
    def validate_split_type(cls, v):
        if v not in ['equal', 'percentage']:
            raise ValueError('split_type must be either "equal" or "percentage"')
        return v
    
    @validator('splits')
    def validate_splits(cls, v, values):
        if 'split_type' in values and values['split_type'] == 'percentage':
            if not v:
                raise ValueError('splits must be provided for percentage split type')
            total_percentage = sum(split.percentage or 0 for split in v)
            if abs(total_percentage - 100) > 0.01:
                raise ValueError('Percentages must sum to 100')
        return v

class BalanceResponse(BaseModel):
    user_id: int
    user_name: str
    balance: float

class UserBalanceResponse(BaseModel):
    group_id: int
    group_name: str
    balance: float

class ChatbotQuery(BaseModel):
    query: str
    user_context: Optional[Dict[str, Any]] = None

class ChatbotResponse(BaseModel):
    response: str
    context_used: Optional[Dict[str, Any]] = None


# Helper function to get context data
def get_chatbot_context(db: Session):
    """Get comprehensive context data for the chatbot"""
    try:
        # Get all users
        users = db.query(User).all()
        users_data = [{"id": user.id, "name": user.name, "email": user.email} for user in users]
        
        # Get all groups with members and expenses
        groups = db.query(Group).all()
        groups_data = []
        
        for group in groups:
            # Calculate total expenses for group
            total_expenses = sum(expense.amount for expense in group.expenses)
            
            # Get recent expenses
            recent_expenses = (
                db.query(Expense)
                .filter(Expense.group_id == group.id)
                .order_by(Expense.created_at.desc())
                .limit(10)
                .all()
            )
            
            expenses_data = []
            for expense in recent_expenses:
                payer = db.query(User).filter(User.id == expense.paid_by).first()
                expenses_data.append({
                    "id": expense.id,
                    "description": expense.description,
                    "amount": expense.amount,
                    "paid_by": {"id": payer.id, "name": payer.name} if payer else None,
                    "split_type": expense.split_type.value,
                    "created_at": expense.created_at.isoformat() if expense.created_at else None
                })
            
            # Get balances for this group
            balances = []
            for user in group.users:
                # Amount user paid
                paid_amount = (
                    db.query(Expense)
                    .filter(and_(Expense.group_id == group.id, Expense.paid_by == user.id))
                    .with_entities(func.sum(Expense.amount))
                    .scalar() or 0
                )
                
                # Amount user owes
                owed_amount = (
                    db.query(ExpenseSplit)
                    .join(Expense)
                    .filter(and_(Expense.group_id == group.id, ExpenseSplit.user_id == user.id))
                    .with_entities(func.sum(ExpenseSplit.amount))
                    .scalar() or 0
                )
                
                balance = paid_amount - owed_amount
                balances.append({
                    "user_id": user.id,
                    "user_name": user.name,
                    "balance": balance,
                    "paid_total": paid_amount,
                    "owes_total": owed_amount
                })
            
            groups_data.append({
                "id": group.id,
                "name": group.name,
                "members": [{"id": user.id, "name": user.name} for user in group.users],
                "total_expenses": total_expenses,
                "recent_expenses": expenses_data,
                "balances": balances
            })
        
        return {
            "users": users_data,
            "groups": groups_data,
            "summary": {
                "total_users": len(users_data),
                "total_groups": len(groups_data),
                "total_expenses": sum(group["total_expenses"] for group in groups_data)
            }
        }
    except Exception as e:
        logger.error(f"Error getting chatbot context: {e}")
        return {}

def generate_chatbot_response(query: str, context: Dict[str, Any]) -> str:
    """Generate response using OpenAI or fallback to rule-based responses"""

    if not DEEPSEEK_API_KEY:
        logger.info("No API key found, using fallback response")
        return generate_fallback_response(query, context)
    
    try:
        # Create system prompt with context
        system_prompt = f"""
You are a helpful assistant for a Splitwise expense-splitting application. You have access to the following data:

CONTEXT DATA:
{json.dumps(context, indent=2)}

Answer user queries about expenses, balances, groups, and users based on this data. 

FORMATTING GUIDELINES:
- Use **bold** for important amounts and names
- Use bullet points (•) for lists
- Use tables when showing multiple balances or expenses
- Use headings (##) to organize sections
- Format monetary amounts as **$XX.XX**
- Use user names instead of IDs when possible

BALANCE INTERPRETATION:
- Positive balance: person is owed money (they should receive)
- Negative balance: person owes money (they should pay)
- Zero balance: person is settled up

Provide specific numbers and details when available. Be conversational and helpful.
If data is not available, clearly mention what's missing.

Current capabilities:
- Check balances for users in groups
- Find recent expenses and who paid
- Show group summaries and member information
- Calculate totals and provide expense breakdowns
"""

        # Use OpenAI API
        client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        logger.info(f"DeepSeek API response generated successfully for query: '{query[:50]}...'")
        return ai_response
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return generate_fallback_response(query, context)

# Replace the generate_fallback_response function

def generate_fallback_response(query: str, context: Dict[str, Any]) -> str:
    """Generate rule-based responses with markdown formatting when API is not available"""
    query_lower = query.lower()
    
    try:
        # Extract context data
        users = context.get("users", [])
        groups = context.get("groups", [])
        
        logger.info(f"Processing fallback for query: '{query}' with {len(users)} users and {len(groups)} groups")
        
        # More flexible pattern matching
        balance_keywords = ["owe", "owes", "balance", "balances", "debt", "money", "amount"]
        expense_keywords = ["expense", "expenses", "paid", "spend", "spending", "cost"]
        recent_keywords = ["recent", "latest", "last", "new"]
        group_keywords = ["group", "groups", "list"]
        
        has_balance = any(keyword in query_lower for keyword in balance_keywords)
        has_expense = any(keyword in query_lower for keyword in expense_keywords)
        has_recent = any(keyword in query_lower for keyword in recent_keywords)
        has_group = any(keyword in query_lower for keyword in group_keywords)
        
        # Find user names in query (more flexible matching)
        found_users = []
        for user in users:
            user_name_variations = [
                user["name"].lower(),
                user["name"].lower().split()[0] if " " in user["name"] else user["name"].lower()
            ]
            if any(variation in query_lower for variation in user_name_variations):
                found_users.append(user)
        
        # Find group names in query (more flexible matching)
        found_groups = []
        for group in groups:
            group_name_lower = group["name"].lower()
            # Check for exact match or partial match
            if group_name_lower in query_lower or any(word in query_lower for word in group_name_lower.split()):
                found_groups.append(group)
        
        # Balance queries
        if has_balance:
            if found_users and found_groups:
                user = found_users[0]
                group = found_groups[0]
                return get_specific_balance(user, group, groups)
            elif found_users:
                user = found_users[0]
                return get_all_user_balances(user, groups)
            elif found_groups:
                group = found_groups[0]
                return get_group_balances_summary(group)
            else:
                return get_all_balances_overview(users, groups)
        
        # Recent expenses queries
        if has_expense and has_recent:
            return get_recent_expenses(groups, limit=5)
        
        # Who paid most queries
        if has_expense and ("most" in query_lower or "top" in query_lower):
            if found_groups:
                group = found_groups[0]
                return get_top_payer_in_group(group)
            else:
                return get_overall_top_payer(groups)
        
        # General expense queries
        if has_expense:
            return get_expenses_summary(groups)
        
        # Group information queries
        if has_group or "list" in query_lower or "show" in query_lower:
            return get_groups_overview(groups)
        
        # Default response with actual data
        return get_default_response_with_data(users, groups, query)
        
    except Exception as e:
        logger.error(f"Fallback response error: {e}")
        return "❌ Sorry, I encountered an error processing your request. Please try again."

# Helper functions for better responses
def get_specific_balance(user: dict, group: dict, groups: list) -> str:
    """Get balance for specific user in specific group"""
    for g in groups:
        if g["id"] == group["id"]:
            for balance in g.get("balances", []):
                if balance["user_name"].lower() == user["name"].lower():
                    amount = abs(balance["balance"])
                    if balance["balance"] > 0:
                        return f"## Balance for **{user['name']}** in **{group['name']}**\n\n**{user['name']}** is owed **${amount:.2f}** in {group['name']}."
                    elif balance["balance"] < 0:
                        return f"## Balance for **{user['name']}** in **{group['name']}**\n\n**{user['name']}** owes **${amount:.2f}** in {group['name']}."
                    else:
                        return f"## Balance for **{user['name']}** in **{group['name']}**\n\n**{user['name']}** is **settled up** in {group['name']}."
    return f"❌ Could not find balance information for **{user['name']}** in **{group['name']}**."

def get_all_user_balances(user: dict, groups: list) -> str:
    """Get all balances for a specific user"""
    total_balance = 0
    group_balances = []
    
    for group in groups:
        for balance in group.get("balances", []):
            if balance["user_name"].lower() == user["name"].lower():
                total_balance += balance["balance"]
                status = "+" if balance["balance"] >= 0 else ""
                group_balances.append(f"• **{group['name']}**: {status}**${balance['balance']:.2f}**")
    
    if group_balances:
        balance_text = "\n".join(group_balances)
        total_status = "+" if total_balance >= 0 else ""
        return f"## **{user['name']}'s** Balance Summary\n\n{balance_text}\n\n**Total Overall**: {total_status}**${total_balance:.2f}**"
    return f"❌ No balance information found for **{user['name']}**."

def get_group_balances_summary(group: dict) -> str:
    """Get balance summary for a specific group"""
    balances = group.get("balances", [])
    if not balances:
        return f"❌ No balance information found for **{group['name']}**."
    
    balance_lines = []
    for balance in balances:
        amount = abs(balance["balance"])
        if balance["balance"] > 0:
            balance_lines.append(f"• **{balance['user_name']}**: is owed **${amount:.2f}**")
        elif balance["balance"] < 0:
            balance_lines.append(f"• **{balance['user_name']}**: owes **${amount:.2f}**")
        else:
            balance_lines.append(f"• **{balance['user_name']}**: is **settled up**")
    
    return f"## 💰 Balances in **{group['name']}**\n\n" + "\n".join(balance_lines)

def get_recent_expenses(groups: list, limit: int = 5) -> str:
    """Get recent expenses across all groups"""
    all_expenses = []
    for group in groups:
        for expense in group.get("recent_expenses", []):
            payer_name = expense.get('paid_by', {}).get('name', 'Unknown') if expense.get('paid_by') else 'Unknown'
            all_expenses.append({
                "text": f"• **${expense['amount']:.2f}** for *{expense['description']}* in **{group['name']}** (paid by **{payer_name}**)",
                "created_at": expense.get('created_at', '')
            })
    
    # Sort by date if available
    all_expenses.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    if all_expenses:
        expense_list = [exp["text"] for exp in all_expenses[:limit]]
        return f"## 📋 Recent Expenses\n\n" + "\n".join(expense_list)
    return "❌ No recent expenses found."

def get_top_payer_in_group(group: dict) -> str:
    """Get top payer in specific group"""
    balances = group.get("balances", [])
    if not balances:
        return f"❌ No payment information found for **{group['name']}**."
    
    max_paid = 0
    top_payer = None
    for balance in balances:
        paid_total = balance.get("paid_total", 0)
        if paid_total > max_paid:
            max_paid = paid_total
            top_payer = balance["user_name"]
    
    if top_payer:
        return f"## 💰 Top Payer in **{group['name']}**\n\n**{top_payer}** has paid the most with **${max_paid:.2f}**."
    return f"❌ No payment information found for **{group['name']}**."

def get_groups_overview(groups: list) -> str:
    """Get overview of all groups"""
    if not groups:
        return "❌ No groups found."
    
    group_list = []
    for group in groups:
        member_count = len(group.get("members", []))
        total_expenses = group.get("total_expenses", 0)
        group_list.append(f"• **{group['name']}**: {member_count} members, **${total_expenses:.2f}** total expenses")
    
    return f"## 👥 Available Groups ({len(groups)})\n\n" + "\n".join(group_list)

def get_default_response_with_data(users: list, groups: list, query: str) -> str:
    """Generate default response with actual data context"""
    return f"""## 🤖 Splitwise Assistant

I found **{len(users)} users** and **{len(groups)} groups** in your data.

You asked: *"{query}"*

### 📊 Quick Overview:
• **Users**: {', '.join([u['name'] for u in users[:3]])}{'...' if len(users) > 3 else ''}
• **Groups**: {', '.join([g['name'] for g in groups[:3]])}{'...' if len(groups) > 3 else ''}

### 💡 Try asking:
• **"How much does {users[0]['name'] if users else '[name]'} owe in {groups[0]['name'] if groups else '[group]'}?"**
• **"Show me recent expenses"**
• **"Who paid the most in {groups[0]['name'] if groups else '[group]'}?"**
• **"List all groups"**
• **"What are {users[0]['name'] if users else '[name]'}'s balances?"**

What would you like to know? 😊"""

# Startup event to initialize database connection
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application starting up...")
    logger.info("Initializing database connection...")
    
    # Try to connect to database
    success = create_engine_with_retry()
    if not success:
        logger.error("Failed to initialize database connection. API will start but database operations will fail.")

# API Endpoints

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "Splitwise API is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        if engine is None:
            return {"status": "unhealthy", "database": "not_initialized", "message": "Database engine not created"}
        
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": f"error: {str(e)}"}

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        db_user = User(name=user.name, email=user.email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Created user: {user.name}")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    """Get all users"""
    try:
        users = db.query(User).all()
        logger.info(f"Retrieved {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/groups", response_model=List[GroupResponse])
def get_all_groups(db: Session = Depends(get_db)):
    """Get all groups"""
    try:
        groups = db.query(Group).all()
        response = []
        
        for group in groups:
            total_expenses = sum(expense.amount for expense in group.expenses)
            response.append(GroupResponse(
                id=group.id,
                name=group.name,
                users=[UserResponse.from_orm(user) for user in group.users],
                total_expenses=total_expenses
            ))
        
        logger.info(f"Retrieved {len(groups)} groups")
        return response
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/groups", response_model=GroupResponse)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    """Create a new group with specified users"""
    try:
        # Verify all users exist
        users = db.query(User).filter(User.id.in_(group.user_ids)).all()
        if len(users) != len(group.user_ids):
            raise HTTPException(status_code=400, detail="One or more users not found")
        
        db_group = Group(name=group.name, users=users)
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        
        # Calculate total expenses
        total_expenses = sum(expense.amount for expense in db_group.expenses)
        
        response = GroupResponse(
            id=db_group.id,
            name=db_group.name,
            users=[UserResponse.from_orm(user) for user in db_group.users],
            total_expenses=total_expenses
        )
        logger.info(f"Created group: {group.name}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/groups/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, db: Session = Depends(get_db)):
    """Get group details including users and total expenses"""
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        total_expenses = sum(expense.amount for expense in group.expenses)
        
        response = GroupResponse(
            id=group.id,
            name=group.name,
            users=[UserResponse.from_orm(user) for user in group.users],
            total_expenses=total_expenses
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/groups/{group_id}/expenses")
def create_expense(group_id: int, expense: ExpenseCreate, db: Session = Depends(get_db)):
    """Add a new expense to a group"""
    try:
        # Verify group exists
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Verify paid_by user is in the group
        if not any(user.id == expense.paid_by for user in group.users):
            raise HTTPException(status_code=400, detail="User who paid is not in the group")
        
        # Create expense
        db_expense = Expense(
            description=expense.description,
            amount=expense.amount,
            group_id=group_id,
            paid_by=expense.paid_by,
            split_type=SplitType(expense.split_type)
        )
        db.add(db_expense)
        db.flush()  # To get the expense ID
        
        # Create expense splits
        if expense.split_type == "equal":
            split_amount = expense.amount / len(group.users)
            for user in group.users:
                split = ExpenseSplit(
                    expense_id=db_expense.id,
                    user_id=user.id,
                    amount=split_amount
                )
                db.add(split)
        else:  # percentage
            for split_input in expense.splits:
                # Verify user is in group
                if not any(user.id == split_input.user_id for user in group.users):
                    raise HTTPException(status_code=400, detail=f"User {split_input.user_id} is not in the group")
                
                split_amount = (split_input.percentage / 100) * expense.amount
                split = ExpenseSplit(
                    expense_id=db_expense.id,
                    user_id=split_input.user_id,
                    amount=split_amount,
                    percentage=split_input.percentage
                )
                db.add(split)
        
        db.commit()
        logger.info(f"Created expense: {expense.description} for group {group_id}")
        return {"message": "Expense created successfully", "expense_id": db_expense.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/groups/{group_id}/balances", response_model=List[BalanceResponse])
def get_group_balances(group_id: int, db: Session = Depends(get_db)):
    """Get balances for all users in a group"""
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        balances = []
        
        for user in group.users:
            # Amount user paid for group expenses
            paid_amount = db.query(Expense).filter(
                and_(Expense.group_id == group_id, Expense.paid_by == user.id)
            ).with_entities(func.sum(Expense.amount)).scalar() or 0
            
            # Amount user owes from expense splits
            owed_amount = db.query(ExpenseSplit).join(Expense).filter(
                and_(Expense.group_id == group_id, ExpenseSplit.user_id == user.id)
            ).with_entities(func.sum(ExpenseSplit.amount)).scalar() or 0
            
            balance = paid_amount - owed_amount
            
            balances.append(BalanceResponse(
                user_id=user.id,
                user_name=user.name,
                balance=balance
            ))
        
        return balances
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group balances: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/users/{user_id}/balances", response_model=List[UserBalanceResponse])
def get_user_balances(user_id: int, db: Session = Depends(get_db)):
    """Get balances for a user across all groups"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        balances = []
        
        for group in user.groups:
            # Amount user paid for this group's expenses
            paid_amount = db.query(Expense).filter(
                and_(Expense.group_id == group.id, Expense.paid_by == user_id)
            ).with_entities(func.sum(Expense.amount)).scalar() or 0
            
            # Amount user owes from expense splits in this group
            owed_amount = db.query(ExpenseSplit).join(Expense).filter(
                and_(Expense.group_id == group.id, ExpenseSplit.user_id == user_id)
            ).with_entities(func.sum(ExpenseSplit.amount)).scalar() or 0
            
            balance = paid_amount - owed_amount
            
            balances.append(UserBalanceResponse(
                group_id=group.id,
                group_name=group.name,
                balance=balance
            ))
        
        return balances
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user balances: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chatbot", response_model=ChatbotResponse)
def chatbot_query(query: ChatbotQuery, db: Session = Depends(get_db)):
    """Process natural language queries about expenses and balances"""
    try:
        logger.info(f"Chatbot query received: '{query.query}'")
        
        # Get comprehensive context
        context = get_chatbot_context(db)
        logger.info(f"Context loaded: {len(context.get('users', []))} users, {len(context.get('groups', []))} groups")
        
        # Generate response
        response_text = generate_chatbot_response(query.query, context)
        
        logger.info(f"Response generated for query: '{query.query[:50]}...' - Length: {len(response_text)}")
        
        return ChatbotResponse(
            response=response_text,
            context_used={
                "users_count": len(context.get("users", [])),
                "groups_count": len(context.get("groups", [])),
                "has_api_key": bool(DEEPSEEK_API_KEY),
                "query_length": len(query.query)
            }
        )
        
    except Exception as e:
        logger.error(f"Chatbot error for query '{query.query}': {e}")
        return ChatbotResponse(
            response="Sorry, I encountered an error processing your request. Please try again later.",
            context_used={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)