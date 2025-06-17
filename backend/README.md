# Splitwise Backend API

A simplified version of Splitwise for tracking shared expenses and balances between users in groups with AI-powered chatbot support.

## Features

- **User Management**: Create and manage users with unique email addresses
- **Group Management**: Create groups with multiple users for expense sharing
- **Expense Management**: Add expenses with equal or percentage-based splits
- **Balance Tracking**: Track who owes whom within groups and across all groups
- **AI Chatbot**: Natural language query support for expenses and balances using DeepSeek API
- **Health Monitoring**: Built-in health checks and database connection monitoring

## Tech Stack

- **FastAPI**: Modern Python web framework with automatic API documentation
- **PostgreSQL**: Database for persistence with connection pooling
- **SQLAlchemy**: ORM for database operations with relationship management
- **Pydantic**: Data validation and serialization
- **DeepSeek API**: AI-powered natural language processing for chatbot
- **Docker**: Containerization for easy deployment and development

## Quick Start

### One-Command Setup

```bash
# Clone and start everything with Docker Compose
git clone <repository-url>
cd NeurixAssignment
docker-compose up --build -d
```

### Verify Setup

```bash
# Check if all services are running
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Access interactive API documentation
open http://localhost:8000/docs
```

### Environment Variables

The `.env` file is already configured with:

```bash
# Database connection
DATABASE_URL=postgresql://postgres:password@postgres:5432/splitwise

# DeepSeek API for AI chatbot (already configured)
DEEPSEEK_API_KEY=<your_api_key>
```

## API Documentation

### Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health Check Endpoints

| Method | Endpoint  | Description                          | Response                                                        |
| ------ | --------- | ------------------------------------ | --------------------------------------------------------------- |
| GET    | `/`       | Basic status check                   | `{"message": "Splitwise API is running!", "status": "healthy"}` |
| GET    | `/health` | Detailed health check with DB status | `{"status": "healthy", "database": "connected"}`                |

### User Management

| Method | Endpoint | Description       | Request Body                                      | Response              |
| ------ | -------- | ----------------- | ------------------------------------------------- | --------------------- |
| POST   | `/users` | Create a new user | `{"name": "Alice", "email": "alice@example.com"}` | User object with ID   |
| GET    | `/users` | Get all users     | -                                                 | Array of user objects |

### Group Management

| Method | Endpoint             | Description                | Request Body                                   | Response                         |
| ------ | -------------------- | -------------------------- | ---------------------------------------------- | -------------------------------- |
| POST   | `/groups`            | Create a group with users  | `{"name": "Roommates", "user_ids": [1, 2, 3]}` | Group object with users          |
| GET    | `/groups`            | Get all groups             | -                                              | Array of group objects           |
| GET    | `/groups/{group_id}` | Get specific group details | -                                              | Group object with total expenses |

### Expense Management

| Method | Endpoint                      | Description          | Request Body               | Response                        |
| ------ | ----------------------------- | -------------------- | -------------------------- | ------------------------------- |
| POST   | `/groups/{group_id}/expenses` | Add expense to group | See expense examples below | Success message with expense ID |

#### Expense Request Examples

**Equal Split:**

```json
{
  "description": "Groceries",
  "amount": 120.0,
  "paid_by": 1,
  "split_type": "equal"
}
```

**Percentage Split:**

```json
{
  "description": "Dinner",
  "amount": 100.0,
  "paid_by": 2,
  "split_type": "percentage",
  "splits": [
    { "user_id": 1, "percentage": 40.0 },
    { "user_id": 2, "percentage": 35.0 },
    { "user_id": 3, "percentage": 25.0 }
  ]
}
```

### Balance Queries

| Method | Endpoint                      | Description                               | Response                      |
| ------ | ----------------------------- | ----------------------------------------- | ----------------------------- |
| GET    | `/groups/{group_id}/balances` | Get balances for all users in a group     | Array of balance objects      |
| GET    | `/users/{user_id}/balances`   | Get balances for a user across all groups | Array of user balance objects |

#### Balance Response Format

**Group Balances:**

```json
[
  {
    "user_id": 1,
    "user_name": "Alice",
    "balance": 25.5 // Positive: owed money, Negative: owes money
  }
]
```

**User Balances:**

```json
[
  {
    "group_id": 1,
    "group_name": "Roommates",
    "balance": -15.75
  }
]
```

### AI Chatbot

| Method | Endpoint   | Description                       | Request Body                                         | Response                        |
| ------ | ---------- | --------------------------------- | ---------------------------------------------------- | ------------------------------- |
| POST   | `/chatbot` | Natural language query processing | `{"query": "How much does Alice owe in Roommates?"}` | Formatted response with context |

#### Chatbot Query Examples

```bash
# Balance queries
curl -X POST "http://localhost:8000/chatbot" \
  -H "Content-Type: application/json" \
  -d '{"query": "How much does Alice owe in Roommates?"}'

# Expense queries
curl -X POST "http://localhost:8000/chatbot" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me recent expenses"}'

# Group information
curl -X POST "http://localhost:8000/chatbot" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who paid the most in Weekend Trip?"}'
```

## Complete API Usage Flow

### 1. Create Users

```bash
# Create Alice
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'

# Create Bob
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "email": "bob@example.com"}'

# Create Charlie
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Charlie", "email": "charlie@example.com"}'
```

### 2. Create Group

```bash
curl -X POST "http://localhost:8000/groups" \
  -H "Content-Type: application/json" \
  -d '{"name": "Roommates", "user_ids": [1, 2, 3]}'
```

### 3. Add Expenses

```bash
# Equal split expense
curl -X POST "http://localhost:8000/groups/1/expenses" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Groceries",
    "amount": 120.0,
    "paid_by": 1,
    "split_type": "equal"
  }'

# Percentage split expense
curl -X POST "http://localhost:8000/groups/1/expenses" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Dinner",
    "amount": 100.0,
    "paid_by": 2,
    "split_type": "percentage",
    "splits": [
      {"user_id": 1, "percentage": 40.0},
      {"user_id": 2, "percentage": 35.0},
      {"user_id": 3, "percentage": 25.0}
    ]
  }'
```

### 4. Check Balances

```bash
# Group balances
curl "http://localhost:8000/groups/1/balances"

# Individual user balances
curl "http://localhost:8000/users/1/balances"
```

### 5. Use AI Chatbot

```bash
curl -X POST "http://localhost:8000/chatbot" \
  -H "Content-Type: application/json" \
  -d '{"query": "How much does Alice owe in Roommates?"}'
```

## Development Setup

### Local Development (Alternative to Docker)

1. **Prerequisites:**

   - Python 3.12+
   - PostgreSQL 15+
   - Git

2. **Setup:**

   ```bash
   # Clone repository
   git clone <repository-url>
   cd NeurixAssignment/backend

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Start PostgreSQL and create database
   createdb splitwise

   # Run the application
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Database Management

```bash
# View database logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U postgres -d splitwise

# Reset database (removes all data)
docker-compose down -v
docker-compose up -d postgres
```

### Application Logs

```bash
# View real-time logs
docker-compose logs -f backend

# View specific log level
docker-compose logs backend | grep ERROR
```

## Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# Test chatbot with different queries
curl -X POST "http://localhost:8000/chatbot" \
  -H "Content-Type: application/json" \
  -d '{"query": "show balances"}'

curl -X POST "http://localhost:8000/chatbot" \
  -H "Content-Type: application/json" \
  -d '{"query": "recent expenses"}'

curl -X POST "http://localhost:8000/chatbot" \
  -H "Content-Type: application/json" \
  -d '{"query": "list groups"}'
```

## Project Structure

```
backend/
├── main.py                 # FastAPI application with all endpoints
├── models.py              # SQLAlchemy database models
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .dockerignore         # Docker ignore rules
├── .env                  # Environment variables (configured)
├── .env.example          # Environment template
├── README.md             # This file
└── __pycache__/          # Python cache (auto-generated)
```

## Database Schema

### Entity Relationships

```
Users ←→ Groups (Many-to-Many via user_groups table)
Users → Expenses (One-to-Many, who paid)
Users → ExpenseSplits (One-to-Many, who owes)
Groups → Expenses (One-to-Many)
Expenses → ExpenseSplits (One-to-Many)
```

### Tables

| Table            | Key Fields                                             | Purpose                   |
| ---------------- | ------------------------------------------------------ | ------------------------- |
| `users`          | id, name, email, created_at                            | Store user information    |
| `groups`         | id, name, created_at                                   | Store group information   |
| `user_groups`    | user_id, group_id                                      | Many-to-many relationship |
| `expenses`       | id, description, amount, group_id, paid_by, split_type | Store expense details     |
| `expense_splits` | id, expense_id, user_id, amount, percentage            | Store individual splits   |

## Key Assumptions Made

### Business Logic

1. **User Email Uniqueness**: Each user must have a unique email address
2. **Group Membership**: Only group members can pay for or be included in group expenses
3. **Balance Calculation**: Balance = Amount Paid - Amount Owed
   - Positive balance = User is owed money
   - Negative balance = User owes money
   - Zero balance = User is settled up
4. **Split Validation**: Percentage splits must sum to exactly 100%
5. **Currency**: All amounts are in a single currency (no multi-currency support)

### Technical Assumptions

1. **Database**: PostgreSQL is available and accessible via Docker
2. **API Keys**: DeepSeek API key is configured and working
3. **Time Zones**: All timestamps stored in UTC
4. **Decimal Precision**: Financial amounts use float (adequate for demo, production would use Decimal)
5. **Concurrency**: No complex locking mechanisms (suitable for demo usage)
6. **Data Validation**: Trust that percentage splits are mathematically valid
7. **Error Handling**: Return HTTP 500 for unexpected database errors

### AI Chatbot Assumptions

1. **Natural Language**: Queries are in English
2. **Context**: Full database context sent to AI (acceptable for demo scale)
3. **Response Format**: Markdown formatting supported in frontend
4. **Rate Limiting**: No rate limiting implemented (would be needed for production)
5. **Fallback Logic**: Rule-based responses when AI API fails

### Security Assumptions

1. **Authentication**: No user authentication implemented (demo purposes)
2. **Authorization**: No access control (all users can see all data)
3. **Data Privacy**: No sensitive data encryption
4. **CORS**: Allows localhost origins for development

### Scalability Assumptions

1. **Data Size**: Designed for small to medium datasets
2. **Concurrent Users**: Limited concurrent user support
3. **API Calls**: No caching layer implemented
4. **File Storage**: No file upload capabilities needed

## AI Chatbot Features

The chatbot can handle natural language queries like:

### Balance Queries

- "How much does Alice owe in Roommates?"
- "What's my balance in Weekend Trip?"
- "Show me all balances for John"

### Expense Queries

- "Show me recent expenses"
- "Who paid the most in Weekend Trip?"
- "What are the latest 3 expenses?"

### Group Information

- "List all groups"
- "Who's in the Roommates group?"
- "What's the total spending in Goa Trip?"

### Response Format

The chatbot returns markdown-formatted responses with:

- **Bold text** for important amounts and names
- Bullet points for lists
- Headers for organization
- Proper currency formatting

## Troubleshooting

### Common Issues

**Database Connection Failed:**

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

**Port Already in Use:**

```bash
# Find process using port 8000
lsof -i :8000  # On Windows: netstat -ano | findstr :8000

# Kill process or change port in docker-compose.yml
```

**AI Chatbot Issues:**

```bash
# Check API key configuration
docker-compose logs backend | grep "DeepSeek"

# Test fallback responses (works without API)
curl -X POST "http://localhost:8000/chatbot" \
  -d '{"query": "list all groups"}'
```

**Percentage Split Errors:**

```bash
# Ensure percentages sum to 100
# Example: 33.33 + 33.33 + 33.34 = 100.00
```

### Performance Optimization

For production deployment, consider:

- Connection pooling configuration
- Database indexing optimization
- API response caching
- Rate limiting implementation
- Background job processing for complex calculations
- Database query optimization with SQLAlchemy

### Support

For issues or questions:

1. Check the interactive API documentation at `/docs`
2. Review application logs with `docker-compose logs backend`
3. Verify environment variables are correctly set
4. Test with provided curl examples
