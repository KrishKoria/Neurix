"""
Chatbot API routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.chatbot import ChatbotService
from app.schemas.chatbot import ChatbotQuery, ChatbotResponse

router = APIRouter(prefix="/chatbot", tags=["chatbot"])
chatbot_service = ChatbotService()


@router.post("/", response_model=ChatbotResponse, summary="Process chatbot query")
def process_chatbot_query(
    query_data: ChatbotQuery,
    db: Session = Depends(get_db)
):
    """
    Process a natural language query about expenses, balances, groups, and users.
    
    - **query**: Natural language question about your expenses and balances
    - **user_context**: Optional context information (not currently used)
    
    ## Example Queries:
    
    ### Balance Queries:
    - "How much does Alice owe in Roommates?"
    - "What are my balances?"
    - "Show balances for Weekend Trip group"
    - "Who owes money in the group?"
    
    ### Expense Queries:
    - "Show me recent expenses"
    - "What did we spend on groceries?"
    - "Who paid the most in Vacation group?"
    - "List all expenses"
    
    ### Group Information:
    - "List all groups"
    - "Who is in the Roommates group?"
    - "Show group summary"
    
    ### General Queries:
    - "What's my total debt?"
    - "Am I settled up?"
    - "Show me everything"
    
    The chatbot uses AI when available (with DeepSeek API key) or falls back to rule-based responses.
    Responses are cached for better performance.
    """
    result = chatbot_service.process_query(db, query_data.query, query_data.user_context)
    
    return ChatbotResponse(
        response=result["response"],
        context_used=result["context_used"],
        cached=result["cached"],
        response_time_ms=result["response_time_ms"]
    )
