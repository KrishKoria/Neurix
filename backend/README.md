# Splitwise Backend API

A simplified version of Splitwise for tracking shared expenses and balances between users in groups.

## Features

- **Group Management**: Create groups with multiple users
- **Expense Management**: Add expenses with equal or percentage-based splits
- **Balance Tracking**: Track who owes whom within groups and across all groups for individual users

## Tech Stack

- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Database for persistence
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **Docker**: Containerization for easy deployment

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the project directory

2. Start the application:

   ```bash
   # On Linux/Mac
   ./start.sh

   # On Windows
   start.bat

   # Or manually
   docker-compose up --build -d
   ```

3. The API will be available at:

   - Backend: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Database: `localhost:5432`

4. Stop the application:

   ```bash
   docker-compose down

   # To also remove database data
   docker-compose down -v
   ```

### View Logs

```bash
docker-compose logs -f backend
docker-compose logs -f postgres
```

### Development Mode

The backend container is configured with volume mounting and auto-reload, so code changes will be reflected immediately.

## Manual Setup (Alternative)

### Prerequisites

- Python 3.8+
- PostgreSQL database

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database:

   - Create a database named `splitwise`
   - Update the `DATABASE_URL` in `main.py` or set it as an environment variable:

   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/splitwise
   ```

3. Run the application:

```bash
uvicorn main:app --reload
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### Health Check

- `GET /`: Basic status check
- `GET /health`: Detailed health check including database connection

### Users

- `POST /users`: Create a new user
- `GET /users`: Get all users

### Groups

- `POST /groups`: Create a new group with users
- `GET /groups/{group_id}`: Get group details with total expenses

### Expenses

- `POST /groups/{group_id}/expenses`: Add expense to group
  - Supports equal and percentage splits

### Balances

- `GET /groups/{group_id}/balances`: Get balances for all users in a group
- `GET /users/{user_id}/balances`: Get balances for a user across all groups

## Example Usage

### 1. Create Users

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
```

### 2. Create Group

```bash
curl -X POST "http://localhost:8000/groups" \
  -H "Content-Type: application/json" \
  -d '{"name": "Roommates", "user_ids": [1, 2, 3]}'
```

### 3. Add Equal Split Expense

```bash
curl -X POST "http://localhost:8000/groups/1/expenses" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Groceries",
    "amount": 120.0,
    "paid_by": 1,
    "split_type": "equal"
  }'
```

### 4. Add Percentage Split Expense

```bash
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

### 5. Get Group Balances

```bash
curl "http://localhost:8000/groups/1/balances"
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://postgres:password@localhost:5432/splitwise`)

## Running Tests

```bash
# With Docker
docker-compose exec backend pytest tests/

# Without Docker
pytest tests/
```

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── models.py            # SQLAlchemy models
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── tests/              # Test suite
│   └── test_main.py
└── README.md
```

## Database Schema

- **Users**: Store user information
- **Groups**: Store group information
- **Expenses**: Store expense details
- **ExpenseSplits**: Store how each expense is split among users
- **UserGroups**: Many-to-many relationship between users and groups
