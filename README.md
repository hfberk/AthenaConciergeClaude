# AI Concierge Platform

A production-ready AI concierge platform designed to scale personalized service for high-net-worth clients. Built with FastAPI, PostgreSQL, Claude AI, and Next.js.

## 🎯 Overview

This platform combines a battle-tested database schema with sophisticated AI agent orchestration, enabling family offices to manage hundreds of client interactions daily while maintaining white-glove service quality.

### Core Capabilities

- **Multi-channel AI Interaction**: Slack, email, and web with conversation threading
- **Comprehensive Client Profiles**: Household relationships and preference tracking
- **Proactive Reminders**: Configurable lead times and delivery channels
- **Project Management**: Automatic task generation and deadline tracking
- **Vetted Recommendations**: Feedback loops for continuous improvement
- **Semantic Search**: Across conversations, preferences, and recommendations

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Vercel    │     │   Railway    │     │  Supabase   │
│  (Next.js)  │────▶│   (FastAPI)  │────▶│ (PostgreSQL)│
│  Frontend   │     │   Backend    │     │  Database   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ┌─────▼─────┐ ┌────▼─────┐
              │   Slack   │ │ Amazon   │
              │    SDK    │ │   SES    │
              └───────────┘ └──────────┘
                    │
              ┌─────▼─────┐
              │  Claude   │
              │ Sonnet 4.5│
              └───────────┘
```

## 📦 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI (Python) | API server & business logic |
| **Database** | PostgreSQL (Supabase) | Data storage + vector search |
| **Frontend** | Next.js 14 (React) | Staff & client web interface |
| **AI Provider** | Claude 4 (Anthropic) | Agent intelligence & reasoning |
| **Agent Framework** | LangGraph | Multi-agent orchestration |
| **Email Service** | Amazon SES | Inbound/outbound email |
| **Chat** | Slack SDK | Real-time messaging |
| **Backend Host** | Railway | Python backend deployment |
| **Frontend Host** | Vercel | Next.js frontend deployment |
| **Storage** | Supabase Storage | File attachments |
| **Auth** | Supabase Auth | User authentication & JWT |

## 🗄️ Database Schema

The platform uses a production-tested schema with **27 tables** organized into **8 logical domains**:

1. **Identity** (3 tables): Organizations, Accounts, Persons
2. **Communication** (4 tables): Identities, Consent, Conversations, Messages
3. **Households** (3 tables): Households, Members, Addresses
4. **Dates & Reminders** (3 tables): Categories, DateItems, ReminderRules
5. **Projects** (3 tables): Projects, Details, Tasks
6. **Recommendations** (6 tables): Vendors, Venues, Restaurants, Products, Recommendations, Feedback
7. **AI Infrastructure** (4 tables): AgentRoster, ExecutionLogs, Embeddings, WorkingMemory
8. **Audit** (1 table): EventLog

See [database/schema_mvp.sql](database/schema_mvp.sql) for the complete schema.

## 🤖 AI Agent System

### Agent Architecture

- **Orchestrator Agent**: Main router that coordinates with specialized sub-agents
- **Retrieval Agent**: Queries database and synthesizes information
- **Recommendation Agent**: Matches preferences with vetted resources
- **Reminder Agent**: Scheduled agent that generates proactive reminders
- **Project Management Agent**: Breaks requests into tasks and tracks progress
- **Data Capture Agent**: Extracts preferences from conversations

### Agent Flow

```
User Message
    ↓
Orchestrator Agent (analyzes intent)
    ↓
[Routes to specialized agent(s)]
    ↓
Context Assembly (client profile, preferences, history)
    ↓
Claude API (reasoning & generation)
    ↓
Response + Database Updates
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or Supabase account)
- Anthropic API key
- (Optional) Slack workspace & app
- (Optional) AWS account for SES

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/athena-concierge.git
cd athena-concierge
```

### 2. Set Up Database

#### Option A: Supabase (Recommended)

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run the schema:
   ```bash
   psql <your-supabase-connection-string> -f database/schema_mvp.sql
   ```

#### Option B: Local PostgreSQL

```bash
createdb concierge_db
psql concierge_db -f database/schema_mvp.sql
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ../.env.example .env

# Edit .env with your credentials:
# - SUPABASE_URL, SUPABASE_SERVICE_KEY, DATABASE_URL
# - ANTHROPIC_API_KEY
# - (Optional) SLACK_BOT_TOKEN, SLACK_APP_TOKEN
# - (Optional) AWS credentials for SES

# Run database migrations (if needed)
# alembic upgrade head

# Start backend server
uvicorn app.main:app --reload
```

Backend will run at `http://localhost:8000`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend will run at `http://localhost:3000`

### 5. Test the System

1. Open `http://localhost:3000` in your browser
2. You should see the staff dashboard
3. API health check at `http://localhost:8000/health`

## 📚 Documentation

### API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Persons
- `GET /api/v1/persons/` - List persons
- `POST /api/v1/persons/` - Create person
- `GET /api/v1/persons/{id}` - Get person details
- `PUT /api/v1/persons/{id}` - Update person
- `DELETE /api/v1/persons/{id}` - Soft delete person

#### Projects
- `GET /api/v1/projects/` - List projects
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `GET /api/v1/projects/{id}/tasks` - List project tasks
- `POST /api/v1/projects/{id}/tasks` - Create task

#### Conversations
- `GET /api/v1/conversations/` - List conversations
- `GET /api/v1/conversations/{id}/messages` - Get messages

#### Agents
- `POST /api/v1/agents/chat` - Send message to AI agent
- `GET /api/v1/agents/health` - Check agent system health

## 🚢 Deployment

### Backend Deployment (Railway)

1. Create Railway account at [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Railway will auto-detect Python and deploy using `Procfile`

### Frontend Deployment (Vercel)

1. Create Vercel account at [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Set `frontend` as root directory
4. Add environment variable: `NEXT_PUBLIC_API_URL=<your-railway-url>`
5. Deploy

### Environment Variables

#### Backend (Railway)
```
DATABASE_URL=<supabase-postgres-url>
SUPABASE_URL=<your-supabase-url>
SUPABASE_SERVICE_KEY=<your-service-key>
ANTHROPIC_API_KEY=<your-anthropic-key>
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ENVIRONMENT=production
```

#### Frontend (Vercel)
```
NEXT_PUBLIC_API_URL=<your-railway-backend-url>
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
cd backend/tests
locust -f load_test.py --host=http://localhost:8000
```

## 🔐 Security

- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Multi-tenancy**: Row-level security with org_id isolation
- **Authentication**: JWT tokens with 1-hour expiration
- **API Keys**: Stored securely, never in code
- **Audit Trail**: Complete logging in event_log and agent_execution_logs

## 📊 Monitoring

### Health Checks

- Backend: `GET /health`
- Database: Included in health check
- Agents: `GET /api/v1/agents/health`

### Logging

Structured logging with `structlog`:
- Request/response logs
- Agent execution logs
- Error tracking with Sentry (optional)

## 🛠️ Development

### Project Structure

```
athena-concierge/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents
│   │   ├── api/             # API routes
│   │   ├── integrations/    # Slack, SES
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   ├── workers/         # Background jobs
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database connection
│   │   └── main.py          # FastAPI app
│   ├── requirements.txt
│   └── Procfile
├── frontend/
│   ├── app/                 # Next.js 14 app router
│   ├── components/          # React components
│   ├── lib/                 # Utilities
│   └── package.json
├── database/
│   └── schema_mvp.sql       # Database schema
├── .env.example
└── README.md
```

### Adding New Agents

1. Create agent file in `backend/app/agents/`
2. Extend `BaseAgent` class
3. Implement `get_system_prompt()` method
4. Add to agent roster in database
5. Update orchestrator routing logic

### Adding New API Endpoints

1. Create route file in `backend/app/api/`
2. Define Pydantic schemas
3. Implement CRUD operations
4. Include router in `app/api/__init__.py`
5. Add corresponding frontend API calls in `frontend/lib/api.ts`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Anthropic for Claude API
- Supabase for managed PostgreSQL
- Railway & Vercel for deployment platforms
- FastAPI & Next.js communities

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Email: support@example.com
- Documentation: [docs.example.com](https://docs.example.com)

---

Built with ❤️ for exceptional client service
