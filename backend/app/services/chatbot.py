"""
Chatbot service with AI integration and caching.
"""
import logging
import time
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.repositories.groups import GroupRepository
from app.repositories.users import UserRepository
from app.repositories.expenses import ExpenseRepository
from app.core.dependencies import cache_manager
from app.core.config import settings
import openai

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service class for AI chatbot functionality."""
    
    def __init__(self):
        self.group_repo = GroupRepository()
        self.user_repo = UserRepository()
        self.expense_repo = ExpenseRepository()
        self.cache = cache_manager
    
    def process_query(self, db: Session, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process chatbot query with caching and AI integration."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"chatbot:{hash(query)}"
            cached_response = self.cache.get(cache_key)
            
            if cached_response:
                cached_response["cached"] = True
                cached_response["response_time_ms"] = (time.time() - start_time) * 1000
                return cached_response
            
            # Get comprehensive context
            context = self._get_chatbot_context(db)
            logger.info(f"Context loaded: {len(context.get('users', []))} users, {len(context.get('groups', []))} groups")
            
            # Generate response
            response_text = self._generate_response(query, context)
            
            response_data = {
                "response": response_text,
                "context_used": {
                    "users_count": len(context.get("users", [])),
                    "groups_count": len(context.get("groups", [])),
                    "has_api_key": bool(settings.deepseek_api_key),
                    "query_length": len(query)
                },
                "cached": False,
                "response_time_ms": (time.time() - start_time) * 1000
            }
            
            # Cache response
            self.cache.set(cache_key, response_data, ttl=settings.chatbot_response_cache_ttl)
            
            logger.info(f"Response generated for query: '{query[:50]}...' - Time: {response_data['response_time_ms']:.2f}ms")
            return response_data
            
        except Exception as e:
            logger.error(f"Chatbot error for query '{query}': {e}")
            return {
                "response": "Sorry, I encountered an error processing your request. Please try again later.",
                "context_used": {"error": str(e)},
                "cached": False,
                "response_time_ms": (time.time() - start_time) * 1000
            }
    
    def _get_chatbot_context(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive context data for the chatbot."""
        try:
            # Check cache first
            cache_key = "chatbot_context"
            cached_context = self.cache.get(cache_key)
            if cached_context:
                return cached_context
            
            # Get all users
            users = self.user_repo.get_multi(db, limit=1000)
            users_data = [{"id": user.id, "name": user.name, "email": user.email} for user in users]
            
            # Get all groups with detailed information
            groups_data = []
            groups = self.group_repo.get_multi(db, limit=1000)
            
            for group in groups:
                # Get group with full context
                full_group = self.group_repo.get_full_context(db, group.id)
                if not full_group:
                    continue
                
                # Calculate total expenses
                total_expenses = sum(expense.amount for expense in full_group.expenses)
                
                # Get recent expenses (last 10)
                recent_expenses = full_group.expenses[:10]  # Already ordered by created_at desc
                expenses_data = []
                
                for expense in recent_expenses:
                    expenses_data.append({
                        "id": expense.id,
                        "description": expense.description,
                        "amount": expense.amount,
                        "paid_by": {"id": expense.paid_by_user.id, "name": expense.paid_by_user.name},
                        "split_type": expense.split_type.value,
                        "created_at": expense.created_at.isoformat() if expense.created_at else None
                    })
                
                # Calculate balances
                from app.repositories.balances import BalanceRepository
                balance_repo = BalanceRepository()
                balances = balance_repo.get_group_balances(db, group.id)
                
                groups_data.append({
                    "id": full_group.id,
                    "name": full_group.name,
                    "members": [{"id": user.id, "name": user.name} for user in full_group.users],
                    "total_expenses": total_expenses,
                    "recent_expenses": expenses_data,
                    "balances": balances
                })
            
            context = {
                "users": users_data,
                "groups": groups_data,
                "summary": {
                    "total_users": len(users_data),
                    "total_groups": len(groups_data),
                    "total_expenses": sum(group["total_expenses"] for group in groups_data)
                }
            }
            
            # Cache context for 60 seconds
            self.cache.set(cache_key, context, ttl=60)
            return context
            
        except Exception as e:
            logger.error(f"Error getting chatbot context: {e}")
            return {}
    
    def _generate_response(self, query: str, context: Dict[str, Any]) -> str:
        """Generate response using AI or fallback."""
        if not settings.deepseek_api_key:
            logger.info("No API key found, using fallback response")
            return self._generate_fallback_response(query, context)
        
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
            client = openai.OpenAI(
                api_key=settings.deepseek_api_key, 
                base_url=settings.deepseek_base_url
            )

            response = client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=settings.deepseek_max_tokens,
                temperature=settings.deepseek_temperature
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"AI response generated successfully for query: '{query[:50]}...'")
            return ai_response
            
        except Exception as e:
            logger.error(f"AI API error: {e}")
            return self._generate_fallback_response(query, context)
    
    def _generate_fallback_response(self, query: str, context: Dict[str, Any]) -> str:
        """Generate rule-based responses when AI is not available."""
        query_lower = query.lower()
        
        try:
            users = context.get("users", [])
            groups = context.get("groups", [])
            
            logger.info(f"Processing fallback for query: '{query}' with {len(users)} users and {len(groups)} groups")
            
            # Pattern matching for different types of queries
            balance_keywords = ["owe", "owes", "balance", "balances", "debt", "money", "amount"]
            expense_keywords = ["expense", "expenses", "paid", "spend", "spending", "cost"]
            recent_keywords = ["recent", "latest", "last", "new"]
            group_keywords = ["group", "groups", "list"]
            
            has_balance = any(keyword in query_lower for keyword in balance_keywords)
            has_expense = any(keyword in query_lower for keyword in expense_keywords)
            has_recent = any(keyword in query_lower for keyword in recent_keywords)
            has_group = any(keyword in query_lower for keyword in group_keywords)
            
            # Find mentioned users and groups
            found_users = self._find_users_in_query(query_lower, users)
            found_groups = self._find_groups_in_query(query_lower, groups)
            
            # Generate appropriate response
            if has_balance:
                return self._handle_balance_query(found_users, found_groups, users, groups)
            elif has_expense and has_recent:
                return self._handle_recent_expenses_query(groups)
            elif has_expense:
                return self._handle_expense_query(groups)
            elif has_group or "list" in query_lower:
                return self._handle_group_query(groups)
            else:
                return self._handle_default_query(users, groups, query)
                
        except Exception as e:
            logger.error(f"Fallback response error: {e}")
            return "❌ Sorry, I encountered an error processing your request. Please try again."
    
    def _find_users_in_query(self, query_lower: str, users: list) -> list:
        """Find users mentioned in the query."""
        found_users = []
        for user in users:
            user_name_variations = [
                user["name"].lower(),
                user["name"].lower().split()[0] if " " in user["name"] else user["name"].lower()
            ]
            if any(variation in query_lower for variation in user_name_variations):
                found_users.append(user)
        return found_users
    
    def _find_groups_in_query(self, query_lower: str, groups: list) -> list:
        """Find groups mentioned in the query."""
        found_groups = []
        for group in groups:
            group_name_lower = group["name"].lower()
            if group_name_lower in query_lower or any(word in query_lower for word in group_name_lower.split()):
                found_groups.append(group)
        return found_groups
    
    def _handle_balance_query(self, found_users: list, found_groups: list, users: list, groups: list) -> str:
        """Handle balance-related queries."""
        if found_users and found_groups:
            user = found_users[0]
            group = found_groups[0]
            return self._get_specific_balance(user, group, groups)
        elif found_users:
            user = found_users[0]
            return self._get_all_user_balances(user, groups)
        elif found_groups:
            group = found_groups[0]
            return self._get_group_balances_summary(group)
        else:
            return self._get_all_balances_overview(users, groups)
    
    def _handle_recent_expenses_query(self, groups: list) -> str:
        """Handle recent expenses queries."""
        all_expenses = []
        for group in groups:
            for expense in group.get("recent_expenses", []):
                payer_name = expense.get('paid_by', {}).get('name', 'Unknown') if expense.get('paid_by') else 'Unknown'
                all_expenses.append({
                    "text": f"• **${expense['amount']:.2f}** for *{expense['description']}* in **{group['name']}** (paid by **{payer_name}**)",
                    "created_at": expense.get('created_at', '')
                })
        
        all_expenses.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        if all_expenses:
            expense_list = [exp["text"] for exp in all_expenses[:5]]
            return f"## 📋 Recent Expenses\n\n" + "\n".join(expense_list)
        return "❌ No recent expenses found."
    
    def _handle_expense_query(self, groups: list) -> str:
        """Handle general expense queries."""
        total_expenses = sum(group.get("total_expenses", 0) for group in groups)
        return f"## 💰 Expense Summary\n\nTotal expenses across all groups: **${total_expenses:.2f}**"
    
    def _handle_group_query(self, groups: list) -> str:
        """Handle group listing queries."""
        if not groups:
            return "❌ No groups found."
        
        group_list = []
        for group in groups:
            member_count = len(group.get("members", []))
            total_expenses = group.get("total_expenses", 0)
            group_list.append(f"• **{group['name']}**: {member_count} members, **${total_expenses:.2f}** total expenses")
        
        return f"## 👥 Available Groups ({len(groups)})\n\n" + "\n".join(group_list)
    
    def _handle_default_query(self, users: list, groups: list, query: str) -> str:
        """Handle default/unknown queries."""
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
    
    def _get_specific_balance(self, user: dict, group: dict, groups: list) -> str:
        """Get balance for specific user in specific group."""
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
    
    def _get_all_user_balances(self, user: dict, groups: list) -> str:
        """Get all balances for a specific user."""
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
    
    def _get_group_balances_summary(self, group: dict) -> str:
        """Get balance summary for a specific group."""
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
    
    def _get_all_balances_overview(self, users: list, groups: list) -> str:
        """Get overview of all balances."""
        return f"## 📊 Balance Overview\n\nFound **{len(users)} users** in **{len(groups)} groups**.\n\nPlease specify a user or group for detailed balance information."
