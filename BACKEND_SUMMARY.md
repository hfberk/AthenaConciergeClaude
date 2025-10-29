# AI Concierge Platform - Backend Summary

**Date:** October 27, 2025
**Status:** Phase 1 Complete ✅

---

## Overview

The backend API infrastructure has been successfully built out to support the comprehensive AI Concierge staff portal. All core endpoints for managing clients, important dates, reminders, projects, conversations, and dashboard aggregations are now in place.

---

## Backend Architecture

### Tech Stack
- **Framework:** FastAPI 0.109.0
- **Database:** Supabase PostgreSQL with pgvector
- **ORM:** SQLAlchemy 2.0.25
- **AI:** Anthropic Claude (claude-sonnet-4-20250514)
- **Integrations:** Slack SDK (Socket Mode), AWS SES
- **Background Workers:** Threading-based (Reminder Worker, Proactive Worker)

### Base URL
- Local: `http://localhost:8000`
- API Prefix: `/api/v1`

---

## API Endpoints - Complete Reference

### 1. Persons API
**Base:** `/api/v1/persons`

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|--------------|
| GET | `/` | List persons | `org_id`, `person_type`, `skip`, `limit` |
| GET | `/{person_id}` | Get person by ID | - |
| POST | `/` | Create new person | - |
| PUT | `/{person_id}` | Update person | - |
| DELETE | `/{person_id}` | Soft delete person | - |

**Person Schema:**
```json
{
  "person_id": "uuid",
  "org_id": "uuid",
  "full_name": "string",
  "preferred_name": "string",
  "person_type": "client|staff|family_member",
  "birthday": "YYYY-MM-DD",
  "timezone": "America/New_York",
  "metadata_jsonb": {},
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

---

### 2. Projects API
**Base:** `/api/v1/projects`

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|--------------|
| GET | `/` | List projects | `org_id`, `person_id`, `status`, `skip`, `limit` |
| GET | `/{project_id}` | Get project by ID | - |
| POST | `/` | Create project | - |
| PUT | `/{project_id}` | Update project | - |
| GET | `/{project_id}/tasks` | List tasks for project | - |
| POST | `/{project_id}/tasks` | Create task | - |

**Project Schema:**
```json
{
  "project_id": "uuid",
  "org_id": "uuid",
  "person_id": "uuid",
  "title": "string",
  "description": "string",
  "status": "new|in_progress|completed|cancelled",
  "priority": 1-5,
  "due_date": "YYYY-MM-DD",
  "assigned_to_account_id": "uuid",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

---

### 3. Conversations API
**Base:** `/api/v1/conversations`

| Method | Endpoint | Description | Query Params |
|--------|----------|-------------|--------------|
| GET | `/` | List conversations | `org_id`, `person_id`, `skip`, `limit` |
| GET | `/{conversation_id}` | Get conversation | - |
| GET | `/{conversation_id}/messages` | List messages | `skip`, `limit` |

**Conversation Schema:**
```json
{
  "conversation_id": "uuid",
  "person_id": "uuid",
  "channel_type": "slack|email|sms|web",
  "subject": "string",
  "status": "active|archived",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

---

### 4. Date Items API ⭐ NEW
**Base:** `/api/v1`

| Method | Endpoint | Description | Features |
|--------|----------|-------------|----------|
| GET | `/persons/{id}/date-items` | List person's dates | Filter by category, upcoming_only |
| GET | `/date-items/{id}` | Get single date | Includes reminder_rules |
| POST | `/date-items` | Create date + reminders | Batch create reminders |
| PUT | `/date-items/{id}` | Update date | Auto-updates next_occurrence |
| DELETE | `/date-items/{id}` | Delete date | Cascades to reminders |
| GET | `/date-items/{id}/reminders` | Get date's reminders | - |

**Date Item Schema:**
```json
{
  "date_item_id": "uuid",
  "org_id": "uuid",
  "person_id": "uuid",
  "category_id": "uuid",
  "title": "Mom's Birthday",
  "date_value": "1985-03-15",
  "recurrence_rule": "FREQ=YEARLY",
  "next_occurrence": "2026-03-15",
  "notes": "She loves surprise parties",
  "metadata_jsonb": {},
  "reminder_rules": [
    {
      "reminder_rule_id": "uuid",
      "reminder_type": "lead_time",
      "lead_time_days": 14,
      "scheduled_datetime": "2026-03-01T09:00:00-05:00",
      "sent_at": null
    }
  ],
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

**Creating Date with Reminders:**
```json
POST /api/v1/date-items
{
  "person_id": "uuid",
  "org_id": "uuid",
  "category_id": "uuid",
  "title": "Driver's License Renewal",
  "date_value": "2026-08-20",
  "recurrence_rule": null,
  "notes": "Bring passport and proof of address",
  "reminder_rules": [
    {
      "reminder_type": "lead_time",
      "lead_time_days": 30,
      "channel_type": "slack"
    },
    {
      "reminder_type": "lead_time",
      "lead_time_days": 7,
      "channel_type": "slack"
    }
  ]
}
```

---

### 5. Reminders API ⭐ NEW
**Base:** `/api/v1/reminders`

| Method | Endpoint | Description | Features |
|--------|----------|-------------|----------|
| GET | `/` | List reminders | Filter: `person_id`, `status_filter` (all/pending/sent) |
| GET | `/{id}` | Get reminder | - |
| POST | `/` | Create reminder | Standalone or linked to date_item |
| PUT | `/{id}` | Update reminder | Cannot update if already sent |
| DELETE | `/{id}` | Delete reminder | Soft delete |
| GET | `/{id}/history` | Delivery history | Includes sent messages |
| POST | `/{id}/retry` | Retry failed reminder | Resets sent_at, reschedules |

**Reminder Rule Schema:**
```json
{
  "reminder_rule_id": "uuid",
  "org_id": "uuid",
  "date_item_id": "uuid",  // Optional - can be null for standalone
  "comm_identity_id": "uuid",
  "reminder_type": "lead_time|scheduled",
  "lead_time_days": 14,  // For lead_time type
  "scheduled_datetime": "2026-03-01T09:00:00-05:00",  // Calculated or explicit
  "sent_at": null,  // null = pending, timestamp = sent
  "metadata_jsonb": {
    "action": "Remind about birthday",
    "created_by": "reminders_api",
    "delivery_status": "pending",
    "manually_retried": false
  },
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

**Types of Reminders:**
- **lead_time:** Send X days before a date_item (e.g., "14 days before birthday")
- **scheduled:** Send at specific datetime (e.g., "tomorrow at 3pm")

---

### 6. Date Categories API ⭐ NEW
**Base:** `/api/v1/date-categories`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List categories for org |
| GET | `/{id}` | Get category |
| POST | `/` | Create category |
| PUT | `/{id}` | Update category |
| DELETE | `/{id}` | Delete (protected if in use) |

**Pre-Seeded Categories:**
- 🎂 Birthday
- 💑 Anniversary
- 🎾 Club Renewal
- 🏠 Property Maintenance
- 🎓 School Event
- ✈️ Travel

**Category Schema:**
```json
{
  "category_id": "uuid",
  "org_id": "uuid",
  "category_name": "Birthday",
  "icon": "🎂",
  "color": "#FF6B6B",
  "schema_jsonb": {},
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

---

### 7. Dashboard API ⭐ NEW
**Base:** `/api/v1`

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/persons/{id}/dashboard` | Comprehensive client view | 5 widget data + stats |
| GET | `/persons/{id}/upcoming` | Upcoming dates | Filter by `days_ahead` (default 30) |
| GET | `/persons/{id}/activity` | Unified activity feed | Conversations, projects, dates |

**Dashboard Response Structure:**
```json
{
  "person": {
    "person_id": "uuid",
    "full_name": "Sarah Chen",
    "preferred_name": "Sarah",
    // ... full person object
  },
  "recent_conversations": [
    {
      "conversation_id": "uuid",
      "channel_type": "slack",
      "last_message_preview": "Can you help me plan...",
      "last_message_at": "2025-10-25T14:30:00Z",
      "message_count": 12
    }
  ],
  "upcoming_dates": [
    {
      "date_item_id": "uuid",
      "title": "Sarah's Birthday",
      "date_value": "1985-03-15",
      "next_occurrence": "2026-03-15",
      "category_name": "Birthday",
      "category_icon": "🎂",
      "days_until": 140,
      "reminder_count": 2
    }
  ],
  "active_projects": [
    {
      "project_id": "uuid",
      "title": "Plan Anniversary Dinner",
      "status": "in_progress",
      "priority": 2,
      "due_date": "2026-06-01",
      "total_tasks": 7,
      "completed_tasks": 4,
      "completion_percentage": 57
    }
  ],
  "recent_recommendations": [
    {
      "recommendation_id": "uuid",
      "venue_name": "The Modern",
      "category": "venue",
      "notes": "Michelin-starred, perfect for anniversary",
      "created_at": "2025-10-20T10:00:00Z"
    }
  ],
  "stats": {
    "total_conversations": 5,
    "total_upcoming_dates": 3,
    "total_active_projects": 2,
    "total_recommendations": 8
  }
}
```

**Use Cases:**
- **Dashboard:** Powers the comprehensive client profile page
- **Upcoming:** Shows upcoming dates in calendar views, reminder widgets
- **Activity:** Unified timeline of all client interactions

---

## Database Schema

### Core Tables (Existing)
- `organizations` - Multi-tenant org structure
- `persons` - Clients, staff, family members
- `accounts` - Staff accounts with auth
- `comm_identities` - Person's communication channels (Slack, email, SMS, phone, web)
- `conversations` - Thread metadata
- `messages` - Individual messages with full history
- `projects` - Client projects
- `tasks` - Project tasks
- `date_categories` - Types of important dates
- `date_items` - Important dates (birthdays, renewals, etc.)
- `reminder_rules` - When/how to send reminders
- `recommendations` - AI-generated recommendations
- `vendors`, `venues`, `restaurants`, `products` - Recommendation items
- `agent_roster` - AI agent configurations
- `agent_execution_logs` - AI execution history

### Key Relationships
```
persons (1) ─── (many) date_items
date_items (1) ─── (many) reminder_rules
date_categories (1) ─── (many) date_items
persons (1) ─── (many) comm_identities
reminder_rules (1) ─── (1) comm_identity
persons (1) ─── (many) projects
projects (1) ─── (many) tasks
projects (1) ─── (many) recommendations
persons (1) ─── (many) conversations
conversations (1) ─── (many) messages
```

---

## Background Workers

### 1. Reminder Worker
**File:** `/backend/app/workers/reminder_worker.py`
**Agent:** `/backend/app/agents/reminder.py`

- **Frequency:** Every 5 minutes (configurable via `REMINDER_CHECK_INTERVAL`)
- **Function:**
  - Scans for `reminder_rules` where `sent_at IS NULL` and `scheduled_datetime <= NOW()`
  - Builds person context via `ContextBuilder`
  - Generates personalized message using Claude
  - Sends via `ProactiveMessagingService` (Slack/Email)
  - Marks `sent_at` timestamp
- **Status:** ✅ Working

### 2. Proactive Worker
**File:** `/backend/app/workers/proactive_worker.py`
**Agent:** `/backend/app/agents/proactive.py`

- **Frequency:** Daily
- **Function:** Sends proactive recommendations and check-ins
- **Status:** ✅ Working

### 3. Slack Integration
**File:** `/backend/app/integrations/slack_user.py`

- **Mode:** Socket Mode (User token - acts as "Athena Concierge")
- **Function:**
  - Listens for DMs and @mentions
  - Routes to `OrchestratorAgent`
  - Sends responses via `ProactiveMessagingService`
- **Status:** ✅ Working

---

## AI Agents

### Agent Architecture
**Base:** `/backend/app/agents/base.py`
**Orchestrator:** `/backend/app/agents/orchestrator.py`

### 6 Specialized Agents:

1. **ReminderManagementAgent** - Parses natural language reminder requests
2. **ReminderAgent** - Generates contextual reminder messages (scheduled)
3. **RetrievalAgent** - Database queries and information lookup
4. **RecommendationAgent** - Vetted resource matching
5. **ProjectManagementAgent** - Task breakdown and project management
6. **DataCaptureAgent** - Preference extraction from conversations

All agents use Claude Sonnet 4 and have access to `ContextBuilder` for personalized responses.

---

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://...

# Anthropic AI
ANTHROPIC_API_KEY=sk-ant-...

# Slack (all three required for Socket Mode)
SLACK_BOT_TOKEN=xoxb-...
SLACK_USER_TOKEN=xoxp-...
SLACK_APP_TOKEN=xapp-...

# AWS SES (optional, for email)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# App Config
APP_NAME="AI Concierge Platform"
APP_VERSION="2.0.0"
DEBUG=false
FRONTEND_URL=http://localhost:3000
```

---

## Current Database State

### Production Data (as of Oct 27, 2025):
- **Organizations:** 1 (default org)
- **Persons:** 1 (Hannah Berkowitz - client)
- **Conversations:** 2 (with message history)
- **Projects:** 0
- **Date Items:** 0 (ready to create via API)
- **Date Categories:** 6 (pre-seeded ✅)
- **Reminder Rules:** 5 (from previous testing)

---

## API Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Test Commands
```bash
# Get organization ID
org_id="00000000-0000-0000-0000-000000000001"

# List persons
curl "http://localhost:8000/api/v1/persons?org_id=$org_id"

# Get date categories
curl "http://localhost:8000/api/v1/date-categories?org_id=$org_id"

# Get person dashboard
person_id="b32ee673-bb2f-4e8f-afd1-fe68bb7b25cd"
curl "http://localhost:8000/api/v1/persons/$person_id/dashboard"

# List reminders (pending only)
curl "http://localhost:8000/api/v1/reminders?org_id=$org_id&status_filter=pending"

# Get upcoming dates (next 30 days)
curl "http://localhost:8000/api/v1/persons/$person_id/upcoming?days_ahead=30"
```

---

## File Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Settings (env vars)
│   ├── database.py                 # Supabase connection
│   ├── api/
│   │   ├── __init__.py            # Router registration
│   │   ├── persons.py             # ✅ Person CRUD
│   │   ├── projects.py            # ✅ Project CRUD + tasks
│   │   ├── conversations.py       # ✅ Conversation + messages
│   │   ├── agents.py              # ✅ Chat interface
│   │   ├── webhooks.py            # ✅ External integrations
│   │   ├── date_items.py          # ⭐ NEW - Date CRUD + reminders
│   │   ├── reminders.py           # ⭐ NEW - Reminder CRUD + history
│   │   ├── date_categories.py     # ⭐ NEW - Category CRUD
│   │   └── dashboard.py           # ⭐ NEW - Aggregated dashboard data
│   ├── agents/                    # AI agents (6 total)
│   ├── models/                    # SQLAlchemy models
│   ├── services/                  # Business logic
│   ├── integrations/              # Slack, SES
│   ├── workers/                   # Background jobs
│   └── utils/
│       └── supabase_helpers.py    # Database query helpers
├── audit_api.py                   # ⭐ NEW - API audit script
└── requirements.txt
```

---

## Performance Considerations

### Current State
- No pagination limits enforced (returns all results)
- No database indexes on new tables
- Reminder worker fetches ALL reminders every 5 minutes

### Recommended Optimizations (TODO)
```sql
-- Pending reminders index
CREATE INDEX idx_pending_reminders
  ON reminder_rules (scheduled_datetime, sent_at)
  WHERE sent_at IS NULL;

-- Person dates index
CREATE INDEX idx_person_dates
  ON date_items (person_id, next_occurrence);

-- Person projects index
CREATE INDEX idx_person_projects
  ON projects (person_id, status);

-- Conversation lookup index
CREATE INDEX idx_conversation_person
  ON conversations (person_id, created_at DESC);
```

---

## Security & Authentication

### Current State
- JWT authentication schema exists but NOT enforced
- All endpoints currently open (no `@requires_auth` decorator)
- Supabase RLS (Row Level Security) NOT enabled
- API relies on `org_id` in query params (trust-based)

### Production Recommendations (TODO)
1. Enable JWT authentication on all endpoints
2. Add role-based access control (admin, concierge, analyst)
3. Enable Supabase RLS policies
4. Add rate limiting (slow-API attacks)
5. Add API key authentication for webhooks

---

## Known Issues & Limitations

### Current Limitations
1. **Recommendations API** - Linked to projects, not persons directly
2. **Recurring Dates** - No automated next_occurrence calculation job
3. **Reminder History** - Basic implementation, message linking could be improved
4. **No Pagination** - Some endpoints return all results
5. **Error Handling** - Generic 500 errors, need more specific error codes

### Future Enhancements
- Add webhook support for Slack events
- Implement reminder delivery tracking (viewed, clicked, dismissed)
- Add bulk operations for reminders
- Implement search across all entities
- Add export functionality (CSV, PDF reports)

---

## Success Metrics

### API Completeness: 100% ✅
- All planned endpoints implemented
- Date Items: 6/6 endpoints ✅
- Reminders: 7/7 endpoints ✅
- Categories: 5/5 endpoints ✅
- Dashboard: 3/3 endpoints ✅

### Testing Status: Partial ⚠️
- Health check: ✅ Working
- Existing APIs (persons, projects, conversations): ✅ Working
- Date categories: ✅ Tested, working
- Dashboard: ⚠️ Fixed bug, needs retest
- Date items: ⏳ Not yet tested
- Reminders: ⏳ Not yet tested

---

## Next Phase: Frontend Development

With the backend complete, the next phase focuses on building the staff frontend:

1. **Enhanced Dashboard Home** - Overview of all clients
2. **Clients Directory** - Searchable list of all clients
3. **Comprehensive Client Profile** - 5-widget dashboard view
4. **Create New Client Flow** - Onboarding form
5. **Date Management UI** - Add/edit dates with reminders
6. **Calendar View** - All dates across all clients
7. **Conversation History** - Full message threads
8. **Project Detail** - Task management interface

---

## Maintenance Notes

### Starting the Backend
```bash
cd /home/runner/workspace/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running the Audit Script
```bash
cd /home/runner/workspace/backend
python audit_api.py
```

### Logs
- Backend logs: Check terminal output or `/tmp/backend.log`
- Structured logging via `structlog`

---

## Contact & Documentation

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Endpoint:** http://localhost:8000/health

---

**Status:** ✅ Backend Phase 1 Complete
**Last Updated:** October 27, 2025
**Next Milestone:** Frontend Development Phase 2
