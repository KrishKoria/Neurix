# Splitwise - Expense Splitting Application

A complete expense splitting application similar to Splitwise, built with modern web technologies and featuring an AI-powered chatbot for natural language queries about expenses and balances.

## 🚀 Features

### Core Functionality

- **👥 User Management**: Create and manage users with unique email addresses
- **🏠 Group Management**: Create groups and manage member relationships
- **💰 Expense Tracking**: Add expenses with equal or percentage-based splits
- **📊 Balance Calculations**: Real-time balance tracking across groups
- **🤖 AI Chatbot**: Natural language queries powered by DeepSeek API

### Technical Highlights

- **Modern Stack**: React 19, FastAPI, PostgreSQL, Docker
- **Type Safety**: Full TypeScript implementation with strict typing
- **Modular Backend**: Layered architecture with repositories, services, and routers
- **API Versioning**: RESTful API with `/api/v1` versioning and legacy support
- **Performance Monitoring**: Request timing, database monitoring, and metrics
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Real-time Health Monitoring**: Automatic backend connectivity checks
- **Interactive API Documentation**: Swagger UI and ReDoc
- **Containerized Deployment**: Complete Docker Compose setup
- **Production Ready**: Rate limiting, error handling, and logging

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│    Frontend     │    │     Backend     │    │    Database     │
│   (React 19)    │◄──►│    (FastAPI)    │◄──►│  (PostgreSQL)   │
│                 │    │                 │    │                 │
│  - TypeScript   │    │  - Modular      │    │  - Connection   │
│  - Tailwind     │    │  - SQLAlchemy   │    │    Pooling      │
│  - Vite         │    │  - Pydantic     │    │  - Health       │
│  - API Client   │    │  - DeepSeek API │    │    Monitoring   │
│  - Chatbot UI   │    │  - Versioned    │    │  - Optimized    │
│                 │    │    APIs         │    │    Queries      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
       :5173                   :8000                   :5432
```

## 🔄 Recent Major Updates

### Backend Optimization & Refactoring

- ✅ **Modular Architecture**: Reorganized into `app/` with layers (core, models, schemas, repositories, services, routers, utils)
- ✅ **API Versioning**: All endpoints now under `/api/v1/` with backward compatibility redirects
- ✅ **Database Optimization**: Added connection pooling, query optimization, eager loading, and indexes
- ✅ **Performance Monitoring**: Request timing, database metrics, and performance headers
- ✅ **Dependency Injection**: Clean dependency management with FastAPI's DI system
- ✅ **Configuration Management**: Environment-based settings with Pydantic
- ✅ **Error Handling**: Comprehensive exception handling and logging
- ✅ **Rate Limiting**: Production-ready rate limiting middleware
- ✅ **Security**: Trusted host middleware and CORS configuration

### Frontend Compatibility Updates

- ✅ **API Integration**: Updated to use versioned API endpoints (`/api/v1/`)
- ✅ **Type Safety**: Enhanced TypeScript types matching backend schemas
- ✅ **Error Handling**: Improved error handling for versioned API responses

## ⚡ Quick Start

### One-Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd NeurixAssignment

# Start everything with Docker Compose
docker-compose up --build -d

# Verify services are running
docker-compose ps
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### Quick Test

```bash
# Test backend health
curl http://localhost:8000/health

# Test frontend accessibility
curl http://localhost:5173

# Create a test user
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
```

## 🛠️ Tech Stack

### Frontend

- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Full type safety and enhanced developer experience
- **Vite**: Fast build tool with hot module replacement
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing and navigation
- **Axios**: HTTP client with interceptors and error handling
- **React Markdown**: Rich text rendering for chatbot responses
- **Lucide React**: Beautiful icons and UI components

### Backend

- **FastAPI**: Modern Python web framework with automatic API documentation
- **SQLAlchemy**: Powerful ORM with relationship management
- **PostgreSQL**: Robust relational database with connection pooling
- **Pydantic**: Data validation and serialization
- **DeepSeek API**: AI-powered natural language processing
- **Python 3.12**: Latest Python with performance improvements

### DevOps & Deployment

- **Docker**: Containerization for consistent environments
- **Docker Compose**: Multi-container orchestration
- **PostgreSQL 15**: Database with health checks and persistence
- **Nginx** (Production ready): Reverse proxy and static file serving

## 📋 Prerequisites

### For Docker Setup (Recommended)

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: For cloning the repository

### For Local Development

- **Node.js**: 18+
- **pnpm**: Package manager
- **Python**: 3.12+
- **PostgreSQL**: 15+

## 🔧 Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Database Configuration (automatically set in Docker)
DATABASE_URL=postgresql://postgres:password@postgres:5432/splitwise

# Frontend API Configuration (automatically set in Docker)
VITE_API_URL=http://localhost:8000
```

### Getting DeepSeek API Key

1. Sign up at [https://platform.deepseek.com/](https://platform.deepseek.com/)
2. Generate an API key
3. Add it to your `.env` file

**Note**: The application works without the API key using fallback responses.

## 🚀 Detailed Setup Instructions

### Option 1: Docker Setup (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd NeurixAssignment

# 2. Create environment file
cp .env.example .env
# Edit .env with your DeepSeek API key

# 3. Start all services
docker-compose up --build -d

# 4. Verify setup
docker-compose ps
curl http://localhost:8000/health
```

### Option 2: Local Development Setup

#### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and create database
createdb splitwise

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend (in new terminal)
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

## 📖 Usage Guide

### 1. Create Users

Navigate to "Create User" or use the API:

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
```

### 2. Create Groups

Navigate to "Create Group" or use the API:

```bash
curl -X POST "http://localhost:8000/groups" \
  -H "Content-Type: application/json" \
  -d '{"name": "Roommates", "user_ids": [1, 2, 3]}'
```

### 3. Add Expenses

#### Equal Split

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

#### Percentage Split

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

### 4. Check Balances

- Navigate to "Group Balances" or "User Balances"
- Use the API endpoints:
  - Group balances: `GET /groups/{id}/balances`
  - User balances: `GET /users/{id}/balances`

### 5. Use AI Chatbot

Click the chat bubble in the bottom-right corner and try queries like:

- "How much does Alice owe in Roommates?"
- "Show me recent expenses"
- "Who paid the most in Weekend Trip?"
- "List all groups"

## 🧪 Testing

### Manual Testing

```bash
# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/

# Test chatbot
curl -X POST "http://localhost:8000/chatbot" \
  -H "Content-Type: application/json" \
  -d '{"query": "show balances"}'

# Test CORS
curl -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: X-Requested-With" \
  -X OPTIONS http://localhost:8000/users
```

### API Testing

Use the interactive documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 API Reference

### Core Endpoints

| Method | Endpoint                | Description                       |
| ------ | ----------------------- | --------------------------------- |
| GET    | `/health`               | Health check with database status |
| POST   | `/users`                | Create a new user                 |
| GET    | `/users`                | List all users                    |
| POST   | `/groups`               | Create a new group                |
| GET    | `/groups`               | List all groups                   |
| POST   | `/groups/{id}/expenses` | Add expense to group              |
| GET    | `/groups/{id}/balances` | Get group balances                |
| GET    | `/users/{id}/balances`  | Get user balances                 |
| POST   | `/chatbot`              | AI chatbot queries                |

### Complete API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **Backend README**: [backend/README.md](backend/README.md)
- **Frontend README**: [frontend/README.md](frontend/README.md)

## 🗄️ Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Groups table
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Many-to-many relationship
CREATE TABLE user_groups (
    user_id INTEGER REFERENCES users(id),
    group_id INTEGER REFERENCES groups(id),
    PRIMARY KEY (user_id, group_id)
);

-- Expenses table
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    description VARCHAR NOT NULL,
    amount DECIMAL NOT NULL,
    group_id INTEGER REFERENCES groups(id),
    paid_by INTEGER REFERENCES users(id),
    split_type VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Expense splits table
CREATE TABLE expense_splits (
    id SERIAL PRIMARY KEY,
    expense_id INTEGER REFERENCES expenses(id),
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL,
    percentage DECIMAL
);
```

## 🔧 Configuration

### Docker Compose Services

```yaml
services:
  frontend: # React app on port 5173
  backend: # FastAPI on port 8000
  postgres: # PostgreSQL on port 5432
```

### Environment Variables

| Variable           | Description                  | Default                 |
| ------------------ | ---------------------------- | ----------------------- |
| `DEEPSEEK_API_KEY` | DeepSeek API key for chatbot | None (uses fallback)    |
| `DATABASE_URL`     | PostgreSQL connection string | Auto-configured         |
| `VITE_API_URL`     | Frontend API endpoint        | `http://localhost:8000` |

## 🚨 Troubleshooting

### Common Issues

#### Port Conflicts

```bash
# Check port usage
lsof -i :5173  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # Database

# Kill processes or change ports in docker-compose.yml
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Reset database (removes all data)
docker-compose down -v
docker-compose up -d postgres
```

#### Chatbot Issues

```bash
# Check API key configuration
docker-compose logs backend | grep -i "deepseek\|api"

# Test without AI (uses fallback responses)
curl -X POST "http://localhost:8000/chatbot" \
  -d '{"query": "list groups"}'
```

#### Build Issues

```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check build logs
docker-compose logs frontend
docker-compose logs backend
```

### Getting Help

1. **Check Logs**: `docker-compose logs [service-name]`
2. **Verify Environment**: `docker-compose exec backend env`
3. **Database Access**: `docker-compose exec postgres psql -U postgres -d splitwise`
4. **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
NeurixAssignment/
├── frontend/                    # React TypeScript frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── lib/               # API service layer
│   │   └── App.tsx            # Main application
│   ├── package.json           # Frontend dependencies
│   └── Dockerfile            # Frontend container config
├── backend/                    # FastAPI Python backend
│   ├── main.py               # API routes and logic
│   ├── models.py             # Database models
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile           # Backend container config
├── docker-compose.yml        # Multi-container orchestration
├── .env.example             # Environment template
└── README.md               # This file
```

## 🎯 Key Features Demonstrated

### Technical Capabilities

- **Full-Stack Development**: React frontend with FastAPI backend
- **Database Integration**: PostgreSQL with SQLAlchemy ORM
- **API Design**: RESTful API with automatic documentation
- **Type Safety**: TypeScript frontend with Pydantic backend validation
- **Containerization**: Docker Compose for easy deployment
- **AI Integration**: DeepSeek API for natural language processing

### Business Logic

- **Multi-user Expense Splitting**: Equal and percentage-based splits
- **Balance Calculations**: Real-time balance tracking with positive/negative indicators
- **Group Management**: Users can belong to multiple groups
- **Natural Language Queries**: AI chatbot for intuitive data access
