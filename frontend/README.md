# Splitwise Frontend

A modern React-based frontend for the Splitwise expense splitting application with AI-powered chatbot support.

## Features

- **Modern React**: Built with React 18, TypeScript, and Vite for fast development
- **Responsive UI**: Clean, mobile-friendly interface using Tailwind CSS
- **Real-time Health Monitoring**: Automatic backend connectivity checks
- **AI Chatbot**: Integrated chatbot with markdown support for natural language queries
- **Interactive Forms**: User-friendly forms for creating users, groups, and expenses
- **Balance Visualization**: Clear display of group and individual balances
- **Navigation**: Intuitive navigation with URL parameter support

## Tech Stack

- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Type-safe development with full type coverage
- **Vite**: Fast build tool with hot module replacement
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Axios**: HTTP client for API communication
- **React Router**: Client-side routing and navigation
- **Lucide React**: Beautiful icons and UI components
- **React Markdown**: Markdown rendering for chatbot responses

## Quick Start

### One-Command Setup

```bash
# Start the entire application (frontend + backend + database)
cd NeurixAssignment
docker-compose up --build -d

# Frontend will be available at http://localhost:5173
```

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd NeurixAssignment/frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev

# Open browser to http://localhost:5173
```

### Verify Setup

```bash
# Check if services are running
docker-compose ps

# Test frontend accessibility
curl http://localhost:5173

# Test backend connectivity from frontend
# Check browser console for "API Base URL" logs
```

## Environment Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```bash
# API endpoint configuration
VITE_API_URL=http://localhost:8000
```

### Docker Environment

The application is configured to work with Docker Compose:

- **Development**: Uses `http://localhost:8000` for API calls
- **Docker**: Uses `http://backend:8000` for internal communication

## Application Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Dashboard.tsx    # Main dashboard with overview
│   │   ├── CreateUser.tsx   # User creation form
│   │   ├── CreateGroup.tsx  # Group creation form
│   │   ├── AddExpense.tsx   # Expense addition form
│   │   ├── GroupBalances.tsx # Group balance viewer
│   │   ├── UserBalances.tsx # User balance viewer
│   │   └── Chatbot.tsx     # AI chatbot component
│   ├── lib/
│   │   └── api.ts          # API service layer
│   ├── App.tsx             # Main application component
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── tsconfig.json          # TypeScript configuration
└── Dockerfile            # Container configuration
```

## Component Documentation

### Core Components

#### App.tsx

- **Purpose**: Main application container with routing and navigation
- **Features**: Health monitoring, responsive navigation, route management
- **Dependencies**: React Router, health check API

#### Dashboard.tsx

- **Purpose**: Overview dashboard showing users, groups, and recent activity
- **Features**: Quick stats, navigation shortcuts, system status
- **API Calls**: Users list, groups list, health check

#### Chatbot.tsx

- **Purpose**: AI-powered chatbot for natural language queries
- **Features**: Markdown rendering, minimizable interface, suggested queries
- **API Calls**: `/chatbot` endpoint with DeepSeek integration

### Form Components

#### CreateUser.tsx

- **Purpose**: User creation with email validation
- **Features**: Form validation, success feedback, ID copying
- **API Calls**: `POST /users`

#### CreateGroup.tsx

- **Purpose**: Group creation with member selection
- **Features**: Multi-user selection, member management
- **API Calls**: `GET /users`, `POST /groups`

#### AddExpense.tsx

- **Purpose**: Expense creation with split type selection
- **Features**: Equal/percentage splits, group member validation
- **API Calls**: `GET /users`, `GET /groups`, `POST /groups/{id}/expenses`

### Balance Components

#### GroupBalances.tsx

- **Purpose**: Display balances for all users in a specific group
- **Features**: Group selection, balance visualization, URL parameters
- **API Calls**: `GET /groups`, `GET /groups/{id}/balances`

#### UserBalances.tsx

- **Purpose**: Display all balances for a specific user across groups
- **Features**: User selection, multi-group balance overview
- **API Calls**: `GET /users`, `GET /users/{id}/balances`

## API Integration

### API Service Layer (`lib/api.ts`)

The frontend uses a centralized API service with the following endpoints:

#### User Management

```typescript
// Create user
POST /users
Body: { name: string, email: string }

// Get all users
GET /users
```

#### Group Management

```typescript
// Create group
POST /groups
Body: { name: string, user_ids: number[] }

// Get all groups
GET /groups

// Get specific group
GET /groups/{id}
```

#### Expense Management

```typescript
// Create expense
POST /groups/{id}/expenses
Body: {
  description: string,
  amount: number,
  paid_by: number,
  split_type: "equal" | "percentage",
  splits?: { user_id: number, percentage: number }[]
}
```

#### Balance Queries

```typescript
// Get group balances
GET / groups / { id } / balances;

// Get user balances
GET / users / { id } / balances;
```

#### AI Chatbot

```typescript
// Query chatbot
POST / chatbot;
Body: {
  query: string;
}
```

#### Health Monitoring

```typescript
// Health check
GET / health;
```

### API Features

- **Automatic Retries**: Built-in retry logic for failed requests
- **Error Handling**: Comprehensive error messages and user feedback
- **Request Logging**: Console logging for debugging API calls
- **Response Interception**: Automatic error parsing and display

## User Interface Features

### Navigation

- **Responsive Design**: Mobile-friendly navigation with collapsible menu
- **Active State**: Visual indication of current page
- **Quick Actions**: Direct links to common tasks

### Forms

- **Real-time Validation**: Immediate feedback on form inputs
- **Loading States**: Visual feedback during API calls
- **Success/Error Messages**: Clear user feedback with actions
- **Auto-population**: URL parameters for pre-filling forms

### Balance Display

- **Color Coding**: Visual distinction between positive/negative balances
- **Currency Formatting**: Proper monetary display with symbols
- **Zero Balance Indication**: Special styling for settled accounts

### Chatbot Interface

- **Floating Widget**: Unobtrusive chat bubble in bottom-right corner
- **Minimizable**: Can be minimized while maintaining accessibility
- **Markdown Support**: Rich text formatting in responses
- **Suggested Queries**: Example questions to guide users
- **Message History**: Conversation persistence during session

## Development Scripts

```bash
# Install dependencies
pnpm install

# Start development server with hot reload
pnpm dev

```

## Key Assumptions Made

### Technical Assumptions

1. **Modern Browser Support**: Assumes ES2020+ support and modern JavaScript features
2. **Development Environment**: Designed for development with hot reload and source maps
3. **API Availability**: Assumes backend is running and accessible at configured URL
4. **Network Connectivity**: Requires stable connection to backend API
5. **LocalStorage**: Uses browser localStorage for temporary data (if implemented)

### User Experience Assumptions

1. **Single Currency**: All monetary amounts displayed in single currency format
2. **English Language**: UI text and error messages in English only
3. **Desktop First**: Optimized for desktop usage with mobile responsiveness
4. **Real-time Updates**: Data updates require manual refresh (no WebSocket implementation)
5. **Session Management**: No persistent user sessions or authentication

### API Integration Assumptions

1. **RESTful API**: Backend follows REST conventions for all endpoints
2. **JSON Communication**: All API requests/responses use JSON format
3. **Error Handling**: Backend returns structured error responses
4. **CORS Configuration**: Backend properly configured for cross-origin requests
5. **Response Times**: API calls complete within reasonable timeframes

### Data Assumptions

1. **User Uniqueness**: Users identified by unique email addresses
2. **Group Membership**: Users can belong to multiple groups
3. **Balance Calculation**: Backend handles all balance calculations
4. **Split Validation**: Backend validates percentage splits sum to 100%
5. **Data Persistence**: All data persisted in backend database

### Chatbot Assumptions

1. **Natural Language**: Queries processed in English language
2. **Context Awareness**: Chatbot has access to full application context
3. **Markdown Support**: Responses formatted in markdown for rich display
4. **API Dependency**: Chatbot requires backend API for processing
5. **Fallback Logic**: Graceful degradation when AI service unavailable

### Security Assumptions

1. **No Authentication**: Application runs without user authentication
2. **Public Access**: All data accessible to all users
3. **Development Security**: Security measures appropriate for development/demo
4. **Trust Backend**: Frontend trusts all data received from backend
5. **No Data Encryption**: No client-side encryption of sensitive data

### Performance Assumptions

1. **Small Data Sets**: Optimized for small to medium data volumes
2. **Client-side Filtering**: Minimal client-side data processing
3. **Network Latency**: Designed for local network deployment
4. **Memory Usage**: Assumes adequate browser memory for application state
5. **Concurrent Users**: Single-user application without collision handling

## Troubleshooting

### Common Issues

**Frontend Won't Start:**

```bash
# Check Node.js version
node --version  # Should be 18+

# Clear package cache
pnpm store prune
rm -rf node_modules
pnpm install

# Check port availability
lsof -i :5173  # On Windows: netstat -ano | findstr :5173
```

**API Connection Issues:**

```bash
# Check backend status
curl http://localhost:8000/health

# Verify environment variables
echo $VITE_API_URL

# Check browser console for CORS errors
# Ensure backend CORS configuration includes frontend origin
```

**Build Issues:**

```bash
# Check TypeScript errors
pnpm type-check

# Clear build cache
rm -rf dist
pnpm build

# Check for missing dependencies
pnpm install --frozen-lockfile
```

**Chatbot Not Working:**

```bash
# Verify backend chatbot endpoint
curl -X POST http://localhost:8000/chatbot \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Check for markdown rendering issues
# Ensure react-markdown dependencies installed
```
