# Quick Start Guide

Get the AI Concierge Platform running in under 15 minutes.

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed
- PostgreSQL 15+ (or Supabase account)
- Anthropic API key ([get one here](https://console.anthropic.com/))

## 5-Minute Local Setup

### Step 1: Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/athena-concierge.git
cd athena-concierge

# Copy environment file
cp .env.example .env
```

### Step 2: Set Up Database

**Option A: Supabase (Recommended - 2 minutes)**

1. Go to [supabase.com](https://supabase.com) and create a free project
2. Copy your connection string from Settings > Database
3. Run schema:
   ```bash
   psql "<your-connection-string>" -f database/schema_mvp.sql
   ```

**Option B: Local PostgreSQL (1 minute)**

```bash
createdb concierge_db
psql concierge_db -f database/schema_mvp.sql
```

### Step 3: Configure Environment

Edit `.env` file:

```bash
# Required: Add your credentials
DATABASE_URL=postgresql://user:pass@localhost:5432/concierge_db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
ANTHROPIC_API_KEY=sk-ant-your-key
SECRET_KEY=$(openssl rand -hex 32)

# Optional: Leave blank for now
SLACK_BOT_TOKEN=
AWS_ACCESS_KEY_ID=
```

### Step 4: Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend running at `http://localhost:8000` ✅

### Step 5: Start Frontend

Open new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend running at `http://localhost:3000` ✅

## Test the System

### 1. Check Health

Visit: `http://localhost:8000/health`

Should show:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected"
}
```

### 2. Open Dashboard

Visit: `http://localhost:3000`

You should see the Athena Concierge staff dashboard.

### 3. Test API

```bash
# View API documentation
open http://localhost:8000/docs

# Create a test client
curl -X POST http://localhost:8000/api/v1/persons/ \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "00000000-0000-0000-0000-000000000001",
    "person_type": "client",
    "full_name": "John Doe",
    "preferred_name": "John"
  }'
```

### 4. Test AI Agent

```bash
# Get person_id from previous response
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "<person-id-from-above>",
    "message": "Hello! Can you help me plan a birthday party?"
  }'
```

You should get an AI-generated response! 🎉

## What's Next?

### Add More Data

1. **Add Restaurants**:
   ```sql
   INSERT INTO restaurants (org_id, name, cuisine, neighborhood, rating, price_band)
   VALUES (
     '00000000-0000-0000-0000-000000000001',
     'The French Laundry',
     'French',
     'Napa Valley',
     4.9,
     '$$$$'
   );
   ```

2. **Add Important Dates**:
   ```sql
   -- First get the Birthday category_id
   SELECT category_id FROM date_categories WHERE category_name = 'Birthday';

   INSERT INTO date_items (org_id, person_id, category_id, title, date_value, next_occurrence)
   VALUES (
     '00000000-0000-0000-0000-000000000001',
     '<person-id>',
     '<category-id>',
     'Birthday',
     '1990-05-15',
     '2025-05-15'
   );
   ```

### Enable Integrations

#### Slack Integration

1. Create Slack app: https://api.slack.com/apps
2. Add bot scopes: `chat:write`, `im:read`, `im:history`
3. Enable Socket Mode
4. Add tokens to `.env`:
   ```bash
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   ```
5. Restart backend

#### Email Integration

1. Set up Amazon SES
2. Verify domain
3. Add credentials to `.env`
4. Configure SES to send to your webhook

### Deploy to Production

Follow the [Deployment Guide](docs/DEPLOYMENT.md) to deploy to:
- Railway (backend)
- Vercel (frontend)
- Supabase (database)

## Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check database connection
psql $DATABASE_URL -c "SELECT 1"
```

### Frontend won't start

```bash
# Check Node version
node --version  # Should be 18+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Database errors

```bash
# Verify schema is applied
psql $DATABASE_URL -c "\dt"

# Reapply schema
psql $DATABASE_URL -f database/schema_mvp.sql
```

### API not responding

```bash
# Check backend logs
# Look for errors in terminal running uvicorn

# Verify environment variables
cat .env | grep -v "^#" | grep "="

# Test connection directly
curl http://localhost:8000/health
```

## Common Commands

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload              # Development
uvicorn app.main:app --host 0.0.0.0        # Production
python -m pytest                            # Run tests
python -m app.workers.reminder_worker      # Run worker

# Frontend
cd frontend
npm run dev          # Development
npm run build        # Production build
npm run start        # Production server
npm run lint         # Linting

# Database
psql $DATABASE_URL                                    # Connect
psql $DATABASE_URL -f database/schema_mvp.sql        # Apply schema
psql $DATABASE_URL -c "SELECT COUNT(*) FROM persons" # Query
```

## Project Structure

```
athena-concierge/
├── backend/           # FastAPI Python backend
│   ├── app/
│   │   ├── agents/    # AI agents (orchestrator, retrieval, etc.)
│   │   ├── api/       # REST API endpoints
│   │   ├── models/    # Database models
│   │   └── main.py    # FastAPI app
│   └── requirements.txt
├── frontend/          # Next.js React frontend
│   ├── app/           # Pages and routes
│   ├── components/    # React components
│   └── lib/           # API client
├── database/          # SQL schemas
│   └── schema_mvp.sql
└── docs/              # Documentation
```

## Key Features

- ✅ Multi-agent AI system with Claude 4
- ✅ 27-table production database schema
- ✅ REST API with automatic docs
- ✅ Modern React dashboard
- ✅ Slack integration ready
- ✅ Email integration ready
- ✅ Multi-tenant architecture
- ✅ Comprehensive audit logging
- ✅ Vector search for semantic queries
- ✅ Background worker for reminders

## Resources

- **Full Documentation**: [README.md](README.md)
- **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Development Guide**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000

## Get Help

- 📖 Read the [full documentation](README.md)
- 🐛 [Report issues](https://github.com/yourusername/athena-concierge/issues)
- 💬 Join our community Slack
- 📧 Email: support@example.com

---

Built with ❤️ for exceptional client service
