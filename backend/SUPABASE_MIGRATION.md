# Supabase Migration Guide

## Overview

The application has been migrated from SQLAlchemy + psycopg2 (direct PostgreSQL) to Supabase Python client (REST API via PostgREST). This change enables better compatibility with serverless environments like Replit.

## What Changed

### Database Layer (`app/database.py`)

**Before:** SQLAlchemy engine with direct PostgreSQL connection
**After:** Supabase client using REST API

```python
# Old approach
from sqlalchemy.orm import Session
db = SessionLocal()
persons = db.query(Person).filter(Person.org_id == org_id).all()

# New approach
from supabase import Client
db = get_supabase_client()
persons = db.table('persons').select('*').eq('org_id', str(org_id)).execute()
```

### Helper Functions (`app/utils/supabase_helpers.py`)

Created `SupabaseQuery` class with common query patterns:

- `select_active()` - Query with soft delete filtering
- `get_by_id()` - Fetch single record by ID
- `insert()` - Create new record
- `update()` - Update existing record
- `soft_delete()` - Soft delete a record

### API Endpoints Refactored

1. **✅ `app/api/persons.py`** - Person CRUD operations
2. **✅ `app/api/projects.py`** - Project and Task operations
3. **✅ `app/api/conversations.py`** - Conversation and Message queries
4. **✅ `app/api/agents.py`** - AI agent chat endpoint

### Key Differences

| Aspect | SQLAlchemy | Supabase Client |
|--------|-----------|-----------------|
| Connection | Direct PostgreSQL (port 5432/6543) | REST API (HTTPS) |
| Driver | psycopg2 | httpx |
| Returns | Model objects | Dictionaries |
| Transactions | Session-based | Atomic operations |
| Connection Pooling | Manual (NullPool) | Automatic |

## Migration Pattern

### Query Pattern

```python
# OLD: SQLAlchemy
persons = db.query(Person).filter(
    Person.org_id == org_id,
    Person.deleted_at.is_(None)
).limit(10).all()

# NEW: Supabase
persons = SupabaseQuery.select_active(
    client=db,
    table='persons',
    filters={'org_id': org_id},
    limit=10
)
```

### Create Pattern

```python
# OLD: SQLAlchemy
person = Person(**data)
db.add(person)
db.commit()
db.refresh(person)

# NEW: Supabase
data['person_id'] = uuid4()
data['created_at'] = datetime.utcnow().isoformat()
person = SupabaseQuery.insert(
    client=db,
    table='persons',
    data=data
)
```

### Update Pattern

```python
# OLD: SQLAlchemy
person = db.query(Person).filter(Person.person_id == id).first()
person.name = new_name
db.commit()

# NEW: Supabase
updated_person = SupabaseQuery.update(
    client=db,
    table='persons',
    id_column='person_id',
    id_value=id,
    data={'name': new_name}
)
```

### Delete Pattern

```python
# OLD: SQLAlchemy
person = db.query(Person).filter(Person.person_id == id).first()
person.deleted_at = datetime.utcnow()
db.commit()

# NEW: Supabase
SupabaseQuery.soft_delete(
    client=db,
    table='persons',
    id_column='person_id',
    id_value=id
)
```

## Environment Variables

**Required:**
```bash
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_ANON_KEY=your-anon-key  # Still needed for config
```

**No longer needed (but kept for reference):**
```bash
DATABASE_URL=postgresql://...  # Not used anymore
```

## Files Modified

1. `app/database.py` - Completely refactored to use Supabase client
2. `app/utils/supabase_helpers.py` - **NEW** - Helper functions
3. `app/api/persons.py` - Refactored all endpoints
4. `app/api/projects.py` - Refactored all endpoints
5. `app/api/conversations.py` - Refactored all endpoints
6. `app/api/agents.py` - Refactored chat endpoint
7. `requirements.txt` - Added `supabase==2.22.1`

## ✅ All Files Migrated!

All files have been successfully migrated to Supabase:

- ✅ `app/integrations/slack_user.py` - Migrated to Supabase
- ✅ `app/integrations/slack.py` - Migrated to Supabase
- ✅ `app/services/context_builder.py` - Migrated to Supabase
- ✅ `app/agents/base.py` - Migrated to Supabase
- ✅ `app/agents/reminder.py` - Migrated to Supabase
- ✅ `app/agents/orchestrator.py` - No database queries (extends BaseAgent)
- `app/models/*.py` - SQLAlchemy models (kept for reference only, not used)

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "database": true
}
```

### Test Person Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/persons/ \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "00000000-0000-0000-0000-000000000001",
    "person_type": "client",
    "full_name": "Test User",
    "preferred_name": "Test"
  }'
```

## Benefits

1. **✅ Works on Replit** - No direct PostgreSQL connection needed
2. **✅ Auto connection pooling** - Supabase handles it
3. **✅ Better for serverless** - REST API is ideal for stateless environments
4. **✅ Built-in retry logic** - httpx handles transient network errors
5. **✅ Type safety** - Pydantic models still validate responses

## Considerations

1. **Performance** - REST API adds latency vs direct PostgreSQL (minimal for most use cases)
2. **Complex queries** - Some advanced SQL queries may need refactoring
3. **Transactions** - Each operation is atomic; multi-step transactions need careful handling
4. **Return types** - Now returns dicts instead of model objects

## Next Steps

1. Update any remaining services/agents that query the database
2. Test all endpoints with real data
3. Update any background workers to use Supabase client
4. Remove unused SQLAlchemy model files (optional - kept for reference)

## Rollback (if needed)

If you need to rollback to SQLAlchemy:

1. Restore `app/database.py` from git history
2. Restore API endpoint files from git history
3. Set `DATABASE_URL` environment variable
4. Remove `supabase` from requirements.txt
5. Reinstall dependencies

## Database Schema Migrations

### Migration 002: Add deleted_at Columns (2025-10-23)

**Problem:** Many tables were missing the `deleted_at` column, causing errors when `SupabaseQuery.select_active()` tried to filter by `deleted_at IS NULL`.

**Solution:** Added `deleted_at TIMESTAMPTZ` column to all tables that need soft delete support.

#### Tables Updated:
- Critical (causing errors): `comm_identities`, `conversations`, `messages`, `date_items`, `tasks`, `reminder_rules`, `agent_roster`, `organizations`, `household_members`
- Additional (consistency): `comm_consent`, `date_categories`, `recommendations`, `interaction_feedback`, `embeddings`, `project_details`

#### How to Apply:

**Option 1: Via Supabase Dashboard (Recommended)**
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy the contents of `backend/migrations/002_add_deleted_at_columns.sql`
4. Paste and run the migration
5. Verify success by running the verification query at the end of the file

**Option 2: Via psql CLI**
```bash
psql "postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-1-us-east-2.pooler.supabase.com:6543/postgres" -f backend/migrations/002_add_deleted_at_columns.sql
```

**Option 3: Via Python Script**
```python
from app.database import get_supabase_client

db = get_supabase_client()
with open('backend/migrations/002_add_deleted_at_columns.sql') as f:
    migration_sql = f.read()
    # Note: Supabase Python client doesn't directly support raw SQL
    # Use the dashboard or psql instead
```

#### Verification:
After applying the migration, check that all tables have `deleted_at`:
```sql
SELECT
  table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE column_name = 'deleted_at'
  AND table_schema = 'public'
ORDER BY table_name;
```

You should see 22 tables total with `deleted_at` columns.

#### Testing:
After applying the migration, test the Slack bot:
1. Send a DM to the Slack bot
2. Check logs for any `column deleted_at does not exist` errors
3. Verify the bot responds successfully

## Support

For issues with Supabase client, see:
- Docs: https://supabase.com/docs/reference/python
- GitHub: https://github.com/supabase-community/supabase-py
