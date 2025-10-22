# AI Concierge Platform

## Overview

This is a production-ready AI concierge platform designed for family offices serving high-net-worth clients. The system combines a comprehensive PostgreSQL database schema (27 tables) with sophisticated AI agent orchestration using Claude 4, enabling white-glove personalized service at scale.

The platform handles multi-channel client communication (Slack, email, web), maintains detailed client profiles and preferences, manages complex projects with automatic task generation, provides intelligent recommendations from vetted resources, and proactively sends reminders for important dates.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI (Python 3.11) for REST API server
- **Agent Framework**: LangGraph + Anthropic Claude Sonnet 4 for AI orchestration
- **Multi-Agent System**: Specialized agents (Orchestrator, Retrieval, Recommendation, Reminder, Project Management, Data Capture) coordinate through a router pattern
- **Authentication**: Designed for Supabase Auth integration with RBAC (admin, concierge, analyst roles)

### Frontend Architecture
- **Framework**: Next.js 14 with React 18 and TypeScript
- **State Management**: Zustand for global state, TanStack Query for server state
- **Styling**: Tailwind CSS with custom primary color theme
- **API Communication**: Axios client with centralized endpoint definitions

### Database Design
- **Database**: PostgreSQL 15+ with pgvector extension for semantic search
- **ORM**: SQLAlchemy 2.0 with declarative models
- **Schema Domains**:
  - Identity & Multi-tenancy (organizations, accounts, persons)
  - Communication Infrastructure (comm_identities, conversations, messages, consent tracking)
  - Households & Addresses (household relationships and structured addresses)
  - Dates & Reminders (date_items with iCal RRULE recurrence, reminder_rules)
  - Projects & Tasks (priority tracking, nested task hierarchy)
  - Recommendations & Resources (vendors, venues, restaurants, products with feedback loops)
  - AI Infrastructure (agent_roster, execution_logs, embeddings, working_memory)
- **Multi-tenancy**: All tables scoped by org_id for tenant isolation
- **Soft Deletes**: deleted_at timestamp pattern across all entities
- **Audit Trail**: event_log table and agent_execution_logs for complete traceability

### AI Agent Architecture
- **Orchestrator Agent**: Primary router that receives all client messages and delegates to specialized agents
- **Retrieval Agent**: Queries database and synthesizes information from client profiles, conversations, and history
- **Recommendation Agent**: Matches client preferences with vetted resources (restaurants, venues, vendors, products)
- **Reminder Agent**: Scheduled execution agent that scans for pending reminders and generates contextual messages
- **Project Management Agent**: Breaks complex requests into projects with structured task lists
- **Data Capture Agent**: Extracts structured information from conversations for database enrichment
- **Context Builder Service**: Assembles comprehensive client context (profile, households, recent conversations, upcoming dates, active projects, preferences) for agent consumption
- **Agent Logging**: Every agent execution logged with run_id, turn_index, payload, execution_time, and tokens_used

### Communication Channels
- **Web**: Direct API interaction via Next.js frontend
- **Slack**: Socket Mode integration with slack-bolt for real-time messaging
- **Email**: Amazon SES for inbound/outbound email (SNS notifications → S3 storage → processing)
- **Conversation Threading**: All channels mapped to unified conversations table with message history

### Vector Search & Embeddings
- **Extension**: pgvector for similarity search
- **Model**: OpenAI text-embedding-3-small (1536 dimensions)
- **Use Cases**: Semantic search across conversations, preferences, and recommendations

### Background Workers
- **Reminder Worker**: Scheduled task (5-minute intervals) that scans reminder_rules and sends proactive reminders via appropriate channels
- **Execution**: Standalone Python process using get_db_context() for session management

## External Dependencies

### Core Services
- **Supabase**: Primary PostgreSQL database hosting with pgvector extension (also provides auth infrastructure)
- **Anthropic Claude**: LLM provider for all agent intelligence (claude-sonnet-4-20250514 model)
- **OpenAI**: Embedding generation only (text-embedding-3-small)

### Communication Services
- **Slack**: Workspace integration via Bot Token, App Token, and Socket Mode
- **Amazon SES**: Email service for inbound/outbound messaging with SNS notifications and S3 storage
- **Amazon S3**: Email storage for SES inbound processing

### Infrastructure
- **Redis**: Session caching and working memory TTL (redis://localhost:6379)
- **Deployment Targets**: Replit (full-stack hosting), Supabase (database)

## Replit Configuration

### Port Configuration
- **Frontend**: Runs on port 5000 (Next.js dev server bound to 0.0.0.0:5000)
- **Backend**: Runs on port 8000 (FastAPI/Uvicorn bound to 0.0.0.0:8000)

### Workflows
Two workflows are configured to run the application:
1. **Frontend**: `cd frontend && npm run dev` - Serves the Next.js dashboard on port 5000
2. **Backend**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000` - Runs the FastAPI server on port 8000

### Required Secrets
The following secrets must be configured in Replit Secrets:
- `DATABASE_URL`: PostgreSQL connection string (Supabase)
- `SECRET_KEY`: Application secret key for security
- `ANTHROPIC_API_KEY`: API key for Claude AI
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Supabase service role key
- `SUPABASE_ANON_KEY`: Supabase anonymous key

Optional secrets for integrations:
- `OPENAI_API_KEY`: For embeddings (if using OpenAI)
- `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`: For Slack integration
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `SES_EMAIL`: For email via AWS SES

### CORS Configuration
The backend automatically allows:
- Localhost variants (localhost:3000, localhost:5000, 127.0.0.1:5000)
- Replit preview domains (dynamically added from REPLIT_DEV_DOMAIN environment variable)

### Deployment Configuration
- **Type**: VM (stateful, always running)
- **Build**: `cd frontend && npm run build`
- **Run**: Both backend and frontend servers run concurrently

### Python Dependencies
- FastAPI ecosystem (fastapi, uvicorn, pydantic, pydantic-settings)
- Database (sqlalchemy, psycopg2-binary, alembic, asyncpg, pgvector)
- AI/ML (anthropic, langgraph, langchain, langchain-anthropic, openai)
- Integrations (slack-sdk, slack-bolt, boto3)
- Utilities (python-dotenv, redis, httpx, beautifulsoup4, structlog, sentry-sdk)
- Security (python-jose, passlib)

### Frontend Dependencies
- Next.js 14, React 18, TypeScript 5.3
- Data fetching (@tanstack/react-query, axios)
- UI (tailwindcss, lucide-react, clsx, date-fns)
- State (zustand)