# Development Guide

Guide for developers working on the AI Concierge Platform.

## Development Environment Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or Docker)
- Git
- Code editor (VS Code recommended)

### VS Code Extensions (Recommended)

- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- GitLens

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/athena-concierge.git
cd athena-concierge

# Copy environment files
cp .env.example .env

# Set up backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up frontend
cd ../frontend
npm install

# Set up database
createdb concierge_dev
psql concierge_dev -f ../database/schema_mvp.sql
```

## Project Structure

```
athena-concierge/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # AI agent implementations
│   │   │   ├── base.py     # Base agent class
│   │   │   ├── orchestrator.py
│   │   │   ├── retrieval.py
│   │   │   ├── recommendation.py
│   │   │   └── ...
│   │   ├── api/            # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── persons.py
│   │   │   ├── projects.py
│   │   │   └── ...
│   │   ├── integrations/   # External service integrations
│   │   │   ├── slack.py
│   │   │   └── ses.py
│   │   ├── models/         # SQLAlchemy models
│   │   │   ├── identity.py
│   │   │   ├── communication.py
│   │   │   └── ...
│   │   ├── services/       # Business logic
│   │   │   └── context_builder.py
│   │   ├── workers/        # Background jobs
│   │   │   └── reminder_worker.py
│   │   ├── config.py       # Configuration management
│   │   ├── database.py     # Database connection
│   │   └── main.py         # FastAPI application
│   ├── tests/              # Backend tests
│   ├── requirements.txt
│   └── Procfile
├── frontend/                # Next.js frontend
│   ├── app/                # Next.js 14 app router
│   │   ├── page.tsx        # Home page
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Global styles
│   ├── components/         # React components
│   ├── lib/                # Utilities
│   │   └── api.ts          # API client
│   ├── public/             # Static assets
│   └── package.json
├── database/               # Database schemas
│   └── schema_mvp.sql
├── docs/                   # Documentation
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
├── .env.example            # Example environment file
└── README.md
```

## Development Workflow

### Running Locally

#### Terminal 1: Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: `http://localhost:8000`

API docs: `http://localhost:8000/docs`

#### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at: `http://localhost:3000`

#### Terminal 3: Background Workers (Optional)

```bash
cd backend
source venv/bin/activate
python -m app.workers.reminder_worker
```

### Making Changes

#### Backend Changes

1. **Adding a new API endpoint:**

```python
# backend/app/api/new_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.get("/")
async def list_items(db: Session = Depends(get_db)):
    # Implementation
    return {"items": []}
```

2. **Add to router:**

```python
# backend/app/api/__init__.py
from app.api import new_feature

router.include_router(new_feature.router, prefix="/new-feature", tags=["new-feature"])
```

3. **Test endpoint:**

```bash
curl http://localhost:8000/api/v1/new-feature/
```

#### Frontend Changes

1. **Create new page:**

```typescript
// frontend/app/new-page/page.tsx
export default function NewPage() {
  return <div>New Page</div>
}
```

2. **Add API call:**

```typescript
// frontend/lib/api.ts
export const newFeatureApi = {
  list: () => apiClient.get('/new-feature/'),
}
```

3. **Use in component:**

```typescript
import { newFeatureApi } from '@/lib/api'

const { data } = await newFeatureApi.list()
```

### Database Changes

#### Creating a Migration

```bash
cd backend
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
```

#### Manual SQL Changes

For MVP, edit `database/schema_mvp.sql` directly:

```sql
-- Add new column
ALTER TABLE persons ADD COLUMN nickname VARCHAR(100);

-- Create index
CREATE INDEX idx_persons_nickname ON persons(nickname);
```

Then apply:

```bash
psql concierge_dev -f database/schema_mvp.sql
```

### Testing

#### Backend Tests

```bash
cd backend
pytest

# Run specific test
pytest tests/test_agents.py::test_orchestrator

# With coverage
pytest --cov=app tests/
```

#### Frontend Tests

```bash
cd frontend
npm test

# Watch mode
npm test -- --watch
```

#### Integration Tests

```bash
cd backend
pytest tests/integration/
```

### Code Quality

#### Backend Linting

```bash
cd backend

# Format with black
black app/

# Sort imports
isort app/

# Lint with flake8
flake8 app/

# Type checking
mypy app/
```

#### Frontend Linting

```bash
cd frontend

# ESLint
npm run lint

# Format with Prettier
npm run format
```

## Working with Agents

### Creating a New Agent

1. **Create agent file:**

```python
# backend/app/agents/my_agent.py
from sqlalchemy.orm import Session
from app.agents.base import BaseAgent

class MyAgent(BaseAgent):
    """Description of what this agent does"""

    def __init__(self, db: Session):
        super().__init__(db, agent_name="my_agent")

    def get_system_prompt(self) -> str:
        return """You are a specialized agent for...

Your capabilities:
- Capability 1
- Capability 2

Guidelines:
- Guideline 1
- Guideline 2
"""

    def custom_method(self, query: str, context: dict) -> str:
        """Agent-specific method"""
        return self.execute(query, context)
```

2. **Add to agent roster:**

```sql
INSERT INTO agent_roster (org_id, agent_name, agent_kind, system_prompt, status)
VALUES (
    '<org-id>',
    'my_agent',
    'execution',
    'System prompt here...',
    'active'
);
```

3. **Use agent:**

```python
from app.agents.my_agent import MyAgent

agent = MyAgent(db)
response = agent.custom_method("Query text", context)
```

### Testing Agents

```python
# tests/test_my_agent.py
from app.agents.my_agent import MyAgent

def test_my_agent(db_session):
    agent = MyAgent(db_session)
    context = {"person": {"person_id": "..."}}

    response = agent.custom_method("Test query", context)

    assert response is not None
    assert len(response) > 0
```

## Database Patterns

### Querying with Soft Deletes

Always filter out soft-deleted records:

```python
# Good
persons = db.query(Person).filter(
    Person.org_id == org_id,
    Person.deleted_at.is_(None)
).all()

# Bad - includes deleted records
persons = db.query(Person).filter(
    Person.org_id == org_id
).all()
```

### Multi-Tenancy

Always include org_id in queries:

```python
# Good
project = db.query(Project).filter(
    Project.project_id == project_id,
    Project.org_id == org_id,
    Project.deleted_at.is_(None)
).first()

# Bad - could access other org's data
project = db.query(Project).filter(
    Project.project_id == project_id
).first()
```

### Using JSONB Fields

```python
# Reading
preferences = person.metadata_jsonb.get("dining_preferences", {})

# Writing
person.metadata_jsonb = {
    **person.metadata_jsonb,
    "dining_preferences": {"cuisine": "Italian"}
}
db.commit()

# Querying (PostgreSQL specific)
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import JSONB

persons = db.query(Person).filter(
    Person.metadata_jsonb["interests"].astext.contains("travel")
).all()
```

## Environment Variables

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/concierge_dev
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
SUPABASE_ANON_KEY=xxx

# AI
ANTHROPIC_API_KEY=sk-ant-xxx

# App
SECRET_KEY=<random-string>
APP_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
DEBUG=true
```

### Optional Variables

```bash
# Slack
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_APP_TOKEN=xapp-xxx
SLACK_SIGNING_SECRET=xxx

# AWS SES
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
SES_EMAIL=concierge@example.com

# Redis
REDIS_URL=redis://localhost:6379

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-xxx
EMBEDDING_MODEL=text-embedding-3-small
```

## Common Tasks

### Add New Database Model

1. Create model in appropriate file under `backend/app/models/`
2. Import in `backend/app/models/__init__.py`
3. Create migration: `alembic revision --autogenerate`
4. Apply migration: `alembic upgrade head`

### Add New API Route

1. Create route in `backend/app/api/`
2. Include in `backend/app/api/__init__.py`
3. Add to API client: `frontend/lib/api.ts`
4. Test with Swagger UI: `http://localhost:8000/docs`

### Update Agent Behavior

1. Modify system prompt in agent class
2. Test with sample queries
3. Update agent in database if needed
4. Clear any cached agent definitions

### Add Frontend Component

1. Create component in `frontend/components/`
2. Use in pages under `frontend/app/`
3. Style with Tailwind CSS
4. Test responsiveness

## Debugging

### Backend Debugging

#### VS Code Launch Configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": false,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

#### Logging

```python
import structlog
logger = structlog.get_logger()

logger.info("Message", key="value", another_key=123)
logger.error("Error occurred", error=str(e), exc_info=True)
```

### Frontend Debugging

#### Browser DevTools

- Network tab for API calls
- Console for errors
- React DevTools extension

#### Logging

```typescript
console.log('Debug info:', data)
console.error('Error:', error)
```

### Database Debugging

#### psql Commands

```sql
-- List tables
\dt

-- Describe table
\d persons

-- Show running queries
SELECT * FROM pg_stat_activity;

-- Kill slow query
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = 12345;
```

## Performance Optimization

### Backend

- Use database indexes for frequent queries
- Implement caching with Redis
- Use pagination for large result sets
- Optimize SQL queries with `EXPLAIN ANALYZE`

### Frontend

- Use Next.js Image component for optimized images
- Implement code splitting
- Use React.memo for expensive components
- Lazy load routes

## Git Workflow

### Branching Strategy

```bash
main              # Production-ready code
├── develop       # Integration branch
├── feature/xxx   # Feature branches
├── fix/xxx       # Bug fixes
└── hotfix/xxx    # Production hotfixes
```

### Commit Messages

Follow conventional commits:

```bash
feat: add new recommendation agent
fix: resolve CORS issue in production
docs: update deployment guide
refactor: simplify context builder logic
test: add tests for orchestrator agent
chore: update dependencies
```

### Pull Request Process

1. Create feature branch from `develop`
2. Make changes and commit
3. Write tests
4. Update documentation if needed
5. Push and create PR
6. Request review
7. Address feedback
8. Merge after approval

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Claude API Documentation](https://docs.anthropic.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Supabase Documentation](https://supabase.com/docs)

## Getting Help

- Check existing issues on GitHub
- Read the documentation
- Ask in team chat
- Create new issue with details

---

Happy coding! 🚀
