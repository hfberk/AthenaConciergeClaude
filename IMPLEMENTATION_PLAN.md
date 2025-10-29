# AI Concierge Platform - Detailed Implementation Plan

**Date:** October 27, 2025
**Phase:** Backend Complete → Frontend Development

---

## Table of Contents
1. [Remaining Backend Tasks](#remaining-backend-tasks)
2. [Frontend Development Plan](#frontend-development-plan)
3. [Testing & Validation](#testing--validation)
4. [Performance Optimization](#performance-optimization)
5. [Deployment & DevOps](#deployment--devops)
6. [Timeline & Milestones](#timeline--milestones)

---

## Remaining Backend Tasks

### 1. API Testing & Validation (2-3 hours)

**Objective:** Verify all new endpoints work correctly

#### Test Date Items API
```bash
# Get Hannah's person_id and org_id
person_id="b32ee673-bb2f-4e8f-afd1-fe68bb7b25cd"
org_id="00000000-0000-0000-0000-000000000001"

# Get birthday category ID
category_id=$(curl -s "http://localhost:8000/api/v1/date-categories?org_id=$org_id" | jq -r '.[] | select(.category_name=="Birthday") | .category_id')

# Test: Create date item with reminders
curl -X POST "http://localhost:8000/api/v1/date-items" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "'$person_id'",
    "org_id": "'$org_id'",
    "category_id": "'$category_id'",
    "title": "Hannah'\''s Birthday",
    "date_value": "1990-06-15",
    "recurrence_rule": "FREQ=YEARLY",
    "notes": "Loves chocolate cake",
    "reminder_rules": [
      {
        "reminder_type": "lead_time",
        "lead_time_days": 14,
        "channel_type": "slack"
      },
      {
        "reminder_type": "lead_time",
        "lead_time_days": 1,
        "channel_type": "slack"
      }
    ]
  }'

# Test: List person's date items
curl "http://localhost:8000/api/v1/persons/$person_id/date-items"

# Test: Get upcoming dates (next 90 days)
curl "http://localhost:8000/api/v1/persons/$person_id/upcoming?days_ahead=90"
```

#### Test Reminders API
```bash
# Test: List all reminders
curl "http://localhost:8000/api/v1/reminders?org_id=$org_id"

# Test: List pending reminders only
curl "http://localhost:8000/api/v1/reminders?org_id=$org_id&status_filter=pending"

# Test: List person's reminders
curl "http://localhost:8000/api/v1/reminders?org_id=$org_id&person_id=$person_id"

# Test: Get reminder by ID (replace with actual ID)
reminder_id="<get from list>"
curl "http://localhost:8000/api/v1/reminders/$reminder_id"

# Test: Get reminder history
curl "http://localhost:8000/api/v1/reminders/$reminder_id/history"
```

#### Test Dashboard API
```bash
# Test: Full dashboard
curl "http://localhost:8000/api/v1/persons/$person_id/dashboard" | jq

# Test: Upcoming dates
curl "http://localhost:8000/api/v1/persons/$person_id/upcoming?days_ahead=30" | jq

# Test: Activity feed
curl "http://localhost:8000/api/v1/persons/$person_id/activity?limit=20" | jq
```

**Deliverable:** Test report documenting success/failure of each endpoint

---

### 2. Database Performance Optimization (1-2 hours)

**Objective:** Add indexes for query performance

#### Create SQL Migration Script
**File:** `/home/runner/workspace/database/migrations/001_add_performance_indexes.sql`

```sql
-- Performance indexes for date items and reminders

-- Index for pending reminders (most critical - runs every 5 min)
CREATE INDEX IF NOT EXISTS idx_pending_reminders
  ON reminder_rules (scheduled_datetime, sent_at)
  WHERE sent_at IS NULL AND deleted_at IS NULL;

-- Index for person's date items (client profile page)
CREATE INDEX IF NOT EXISTS idx_person_dates
  ON date_items (person_id, next_occurrence)
  WHERE deleted_at IS NULL;

-- Index for date item's reminders (date detail page)
CREATE INDEX IF NOT EXISTS idx_date_item_reminders
  ON reminder_rules (date_item_id)
  WHERE deleted_at IS NULL;

-- Index for person's projects (client profile page)
CREATE INDEX IF NOT EXISTS idx_person_projects
  ON projects (person_id, status, priority)
  WHERE deleted_at IS NULL;

-- Index for project tasks (project detail page)
CREATE INDEX IF NOT EXISTS idx_project_tasks
  ON tasks (project_id, status, sort_order)
  WHERE deleted_at IS NULL;

-- Index for person's conversations (client profile page)
CREATE INDEX IF NOT EXISTS idx_person_conversations
  ON conversations (person_id, updated_at DESC)
  WHERE deleted_at IS NULL;

-- Index for conversation messages (message thread page)
CREATE INDEX IF NOT EXISTS idx_conversation_messages
  ON messages (conversation_id, created_at)
  WHERE deleted_at IS NULL;

-- Index for comm_identity lookup (reminder delivery)
CREATE INDEX IF NOT EXISTS idx_comm_identity_person
  ON comm_identities (person_id, is_primary)
  WHERE deleted_at IS NULL;

-- Analyze tables for query optimization
ANALYZE reminder_rules;
ANALYZE date_items;
ANALYZE projects;
ANALYZE tasks;
ANALYZE conversations;
ANALYZE messages;
ANALYZE comm_identities;
```

#### Apply Migration
```bash
# Using psql (if available)
psql "$DATABASE_URL" -f database/migrations/001_add_performance_indexes.sql

# OR using Python script
python -c "
from app.database import get_db_context
with open('database/migrations/001_add_performance_indexes.sql') as f:
    sql = f.read()
with get_db_context() as db:
    db.execute(sql)
"
```

**Deliverable:** Migration script executed, indexes created

---

### 3. Enhanced Error Handling (2 hours)

**Objective:** Improve API error responses

#### Create Custom Exception Classes
**File:** `/backend/app/exceptions.py` (NEW)

```python
"""Custom exception classes for better error handling"""

from fastapi import HTTPException, status

class ResourceNotFoundException(HTTPException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with ID {resource_id} not found"
        )

class ValidationException(HTTPException):
    def __init__(self, field: str, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error on field '{field}': {message}"
        )

class ConflictException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )

class DatabaseException(HTTPException):
    def __init__(self, operation: str, details: str = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during {operation}" + (f": {details}" if details else "")
        )
```

**Apply to APIs:** Update endpoints to use custom exceptions instead of generic HTTPException

**Deliverable:** Better error messages for frontend consumption

---

### 4. API Documentation Enhancement (1 hour)

**Objective:** Improve Swagger/OpenAPI docs

#### Add Detailed Docstrings
Update each endpoint with:
- Comprehensive description
- Request/response examples
- Error codes and meanings
- Usage notes

**Example:**
```python
@router.post("/date-items", response_model=DateItemResponse)
async def create_date_item(date_item: DateItemCreate, db: Client = Depends(get_db)):
    """
    Create a new important date with optional reminder rules

    This endpoint creates a date item (birthday, anniversary, license renewal, etc.)
    and optionally creates multiple reminder rules in a single transaction.

    **Reminder Types:**
    - `lead_time`: Send X days before the date (e.g., 14 days before birthday)
    - `scheduled`: Send at specific datetime (must provide scheduled_datetime)

    **Examples:**

    Create birthday with 2 reminders:
    ```json
    {
      "person_id": "uuid",
      "org_id": "uuid",
      "category_id": "uuid",
      "title": "Mom's Birthday",
      "date_value": "1960-05-20",
      "recurrence_rule": "FREQ=YEARLY",
      "reminder_rules": [
        {"reminder_type": "lead_time", "lead_time_days": 14},
        {"reminder_type": "lead_time", "lead_time_days": 1}
      ]
    }
    ```

    **Returns:** Created date item with embedded reminder_rules array

    **Errors:**
    - 404: Person or category not found
    - 400: No comm_identity found for person (cannot send reminders)
    """
    # implementation...
```

**Deliverable:** Enhanced API documentation at `/docs`

---

## Frontend Development Plan

### Phase 2.1: Project Setup & Foundation (2-3 hours)

#### 1. Install Additional Dependencies

```bash
cd /home/runner/workspace/frontend

# UI Components
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install @radix-ui/react-tabs @radix-ui/react-select
npm install @radix-ui/react-avatar @radix-ui/react-badge
npm install @radix-ui/react-tooltip

# Form Handling
npm install react-hook-form @hookform/resolvers zod

# Date/Time
npm install date-fns

# State Management (optional, if needed)
npm install zustand

# Charts/Visualization (for stats)
npm install recharts
```

#### 2. Create Shared UI Components

**File Structure:**
```
frontend/
├── components/
│   ├── ui/                    # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Modal.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Badge.tsx
│   │   ├── Avatar.tsx
│   │   ├── Tabs.tsx
│   │   └── Spinner.tsx
│   ├── layout/                # Layout components
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── PageLayout.tsx
│   └── widgets/               # Dashboard widgets
│       ├── ProfileWidget.tsx
│       ├── ConversationsWidget.tsx
│       ├── ImportantDatesWidget.tsx
│       ├── ProjectsWidget.tsx
│       └── RecommendationsWidget.tsx
```

**Example: Button Component**
```typescript
// components/ui/Button.tsx
import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        default: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
        secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
        outline: 'border border-gray-300 bg-white hover:bg-gray-50 focus:ring-gray-500',
        ghost: 'hover:bg-gray-100 focus:ring-gray-500',
        danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4',
        lg: 'h-12 px-6 text-lg',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={buttonVariants({ variant, size, className })}
        ref={ref}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'

export { Button, buttonVariants }
```

#### 3. Extend API Client

**File:** `/frontend/lib/api.ts`

Add types and methods for new endpoints:

```typescript
// lib/api.ts

import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface DateItem {
  date_item_id: string
  person_id: string
  org_id: string
  category_id: string
  title: string
  date_value: string
  recurrence_rule?: string
  next_occurrence?: string
  notes?: string
  reminder_rules: ReminderRule[]
  created_at: string
  updated_at: string
}

export interface ReminderRule {
  reminder_rule_id: string
  reminder_type: 'lead_time' | 'scheduled'
  lead_time_days?: number
  scheduled_datetime?: string
  sent_at?: string
  created_at: string
}

export interface DateCategory {
  category_id: string
  org_id: string
  category_name: string
  icon?: string
  color?: string
}

export interface PersonDashboard {
  person: Person
  recent_conversations: ConversationSummary[]
  upcoming_dates: UpcomingDateItem[]
  active_projects: ActiveProjectSummary[]
  recent_recommendations: RecommendationSummary[]
  stats: {
    total_conversations: number
    total_upcoming_dates: number
    total_active_projects: number
    total_recommendations: number
  }
}

// API Methods

export const dateItemsApi = {
  // List person's date items
  listByPerson: (personId: string, params?: {
    category_id?: string
    upcoming_only?: boolean
  }) =>
    apiClient.get<DateItem[]>(`/persons/${personId}/date-items`, { params }),

  // Get single date item
  get: (dateItemId: string) =>
    apiClient.get<DateItem>(`/date-items/${dateItemId}`),

  // Create date item with reminders
  create: (data: {
    person_id: string
    org_id: string
    category_id: string
    title: string
    date_value: string
    recurrence_rule?: string
    notes?: string
    reminder_rules?: Array<{
      reminder_type: 'lead_time' | 'scheduled'
      lead_time_days?: number
      scheduled_datetime?: string
      channel_type?: string
    }>
  }) =>
    apiClient.post<DateItem>('/date-items', data),

  // Update date item
  update: (dateItemId: string, data: Partial<DateItem>) =>
    apiClient.put<DateItem>(`/date-items/${dateItemId}`, data),

  // Delete date item
  delete: (dateItemId: string) =>
    apiClient.delete(`/date-items/${dateItemId}`),
}

export const remindersApi = {
  // List reminders
  list: (params: {
    org_id: string
    person_id?: string
    status_filter?: 'all' | 'pending' | 'sent'
  }) =>
    apiClient.get<ReminderRule[]>('/reminders', { params }),

  // Get reminder
  get: (reminderId: string) =>
    apiClient.get<ReminderRule>(`/reminders/${reminderId}`),

  // Get reminder history
  getHistory: (reminderId: string) =>
    apiClient.get(`/reminders/${reminderId}/history`),

  // Retry reminder
  retry: (reminderId: string) =>
    apiClient.post(`/reminders/${reminderId}/retry`),
}

export const categoriesApi = {
  // List categories
  list: (orgId: string) =>
    apiClient.get<DateCategory[]>('/date-categories', {
      params: { org_id: orgId }
    }),

  // Create category
  create: (data: {
    org_id: string
    category_name: string
    icon?: string
    color?: string
  }) =>
    apiClient.post<DateCategory>('/date-categories', data),
}

export const dashboardApi = {
  // Get person dashboard
  getPersonDashboard: (personId: string) =>
    apiClient.get<PersonDashboard>(`/persons/${personId}/dashboard`),

  // Get upcoming dates
  getUpcoming: (personId: string, daysAhead: number = 30) =>
    apiClient.get(`/persons/${personId}/upcoming`, {
      params: { days_ahead: daysAhead }
    }),

  // Get activity feed
  getActivity: (personId: string, limit: number = 50) =>
    apiClient.get(`/persons/${personId}/activity`, {
      params: { limit }
    }),
}

// Export existing APIs
export { personsApi, projectsApi, conversationsApi, agentsApi } from './existing-api'
```

**Deliverable:** Reusable UI components + Extended API client

---

### Phase 2.2: Enhanced Dashboard Home (3-4 hours)

**File:** `/frontend/app/page.tsx`

**Objective:** Create an overview showing all clients who need attention

```typescript
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { personsApi, dashboardApi } from '@/lib/api'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { Calendar, Users, CheckSquare, AlertCircle } from 'lucide-react'

export default function DashboardHome() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [clients, setClients] = useState([])
  const [stats, setStats] = useState({
    totalClients: 0,
    totalProjects: 0,
    upcomingDates: 0,
    needsAttention: 0
  })

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      // Load all clients
      const orgId = '00000000-0000-0000-0000-000000000001'
      const response = await personsApi.list({ org_id: orgId, person_type: 'client' })
      const clientsData = response.data

      // Get dashboard data for each client (parallel)
      const dashboardPromises = clientsData.map(client =>
        dashboardApi.getPersonDashboard(client.person_id)
          .then(res => ({ client, dashboard: res.data }))
          .catch(() => ({ client, dashboard: null }))
      )

      const dashboards = await Promise.all(dashboardPromises)

      // Calculate who needs attention
      const clientsNeedingAttention = dashboards.map(({ client, dashboard }) => {
        const needsAttention = []

        if (dashboard) {
          // No contact in 7 days
          if (dashboard.recent_conversations.length > 0) {
            const lastContact = new Date(dashboard.recent_conversations[0].last_message_at)
            const daysSinceContact = (Date.now() - lastContact.getTime()) / (1000 * 60 * 60 * 24)
            if (daysSinceContact > 7) {
              needsAttention.push(`No contact in ${Math.floor(daysSinceContact)} days`)
            }
          }

          // Upcoming dates this week
          const datesThisWeek = dashboard.upcoming_dates.filter(d => d.days_until <= 7)
          if (datesThisWeek.length > 0) {
            needsAttention.push(`${datesThisWeek.length} date(s) this week`)
          }

          // Project due soon
          const projectsDueSoon = dashboard.active_projects.filter(p => {
            if (!p.due_date) return false
            const daysUntilDue = (new Date(p.due_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
            return daysUntilDue <= 7 && daysUntilDue >= 0
          })
          if (projectsDueSoon.length > 0) {
            needsAttention.push(`${projectsDueSoon.length} project(s) due soon`)
          }
        }

        return {
          ...client,
          needsAttention,
          dashboard
        }
      }).filter(c => c.needsAttention.length > 0)

      setClients(clientsNeedingAttention)
      setStats({
        totalClients: clientsData.length,
        totalProjects: dashboards.reduce((sum, d) => sum + (d.dashboard?.stats.total_active_projects || 0), 0),
        upcomingDates: dashboards.reduce((sum, d) => sum + (d.dashboard?.stats.total_upcoming_dates || 0), 0),
        needsAttention: clientsNeedingAttention.length
      })
    } catch (error) {
      console.error('Failed to load dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">AI Concierge - Staff Portal</h1>
        <p className="text-gray-600 mt-2">Manage client relationships and track important dates</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Clients</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalClients}</p>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Projects</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalProjects}</p>
            </div>
            <CheckSquare className="w-10 h-10 text-green-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Upcoming Dates</p>
              <p className="text-3xl font-bold text-gray-900">{stats.upcomingDates}</p>
            </div>
            <Calendar className="w-10 h-10 text-purple-500" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Need Attention</p>
              <p className="text-3xl font-bold text-red-600">{stats.needsAttention}</p>
            </div>
            <AlertCircle className="w-10 h-10 text-red-500" />
          </div>
        </Card>
      </div>

      {/* Clients Needing Attention */}
      <Card className="p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Clients Needing Attention</h2>
          <Button
            variant="outline"
            onClick={() => router.push('/clients')}
          >
            View All Clients
          </Button>
        </div>

        {clients.length === 0 ? (
          <p className="text-gray-500">All clients are up to date! 🎉</p>
        ) : (
          <div className="space-y-4">
            {clients.map(client => (
              <div
                key={client.person_id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition"
                onClick={() => router.push(`/clients/${client.person_id}`)}
              >
                <div>
                  <p className="font-semibold text-gray-900">{client.full_name}</p>
                  <div className="flex gap-2 mt-2">
                    {client.needsAttention.map((reason, idx) => (
                      <Badge key={idx} variant="warning">
                        {reason}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Button variant="ghost" size="sm">
                  View Profile →
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 hover:shadow-lg transition cursor-pointer" onClick={() => router.push('/clients/new')}>
          <h3 className="font-semibold text-gray-900 mb-2">+ New Client</h3>
          <p className="text-sm text-gray-600">Add a new client to the system</p>
        </Card>

        <Card className="p-6 hover:shadow-lg transition cursor-pointer" onClick={() => router.push('/clients')}>
          <h3 className="font-semibold text-gray-900 mb-2">View All Clients</h3>
          <p className="text-sm text-gray-600">Browse and search all clients</p>
        </Card>

        <Card className="p-6 hover:shadow-lg transition cursor-pointer" onClick={() => router.push('/calendar')}>
          <h3 className="font-semibold text-gray-900 mb-2">Calendar View</h3>
          <p className="text-sm text-gray-600">See all important dates</p>
        </Card>
      </div>
    </div>
  )
}
```

**Deliverable:** Functional dashboard home page showing clients needing attention

---

### Phase 2.3: Clients Directory (3 hours)

**File:** `/frontend/app/clients/page.tsx`

**Features:**
- List all clients
- Search by name
- Filter by client type
- Sort by last contact, name, join date
- Show quick stats per client (upcoming dates, active projects)
- Click to view profile

**Key Implementation Points:**
- Client-side search/filter for performance
- Pagination (20 clients per page)
- Empty state when no clients
- Loading skeleton

**Deliverable:** Searchable, filterable client directory

---

### Phase 2.4: Comprehensive Client Profile (8-10 hours)

**File:** `/frontend/app/clients/[id]/page.tsx`

**This is the CORE feature - 5 widgets:**

#### Widget 1: Profile Info (editable)
- Name, birthday, timezone, contact methods
- Edit inline or via modal
- Household information
- Care notes

#### Widget 2: Recent Conversations
- Last 5 conversations
- Channel icon, timestamp, preview
- Click to view full thread
- [View All Conversations] button

#### Widget 3: Upcoming Important Dates
- Next 5 upcoming dates
- Category icon, days until, reminder count
- [+ Add Important Date] button opens modal
- [View All Dates] button

#### Widget 4: Active Projects
- Current projects with progress bars
- Task completion count
- Due dates
- [+ Create Project] button
- [View Details] for each project

#### Widget 5: AI Recommendations
- Recent recommendations
- Venue/vendor names
- Rationale notes
- [View All] button

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ ← Back to Clients                                       │
│                                                         │
│ Sarah Chen                    [Edit Profile] [Actions▼]│
├─────────────────┬───────────────────────────────────────┤
│ PROFILE INFO    │ RECENT CONVERSATIONS                  │
│ (Widget 1)      │ (Widget 2)                            │
│                 │                                       │
│                 ├───────────────────────────────────────┤
│                 │ UPCOMING IMPORTANT DATES              │
│                 │ (Widget 3)                            │
│                 │                                       │
├─────────────────┴───────────────────────────────────────┤
│ ACTIVE PROJECTS (Widget 4)                              │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ AI RECOMMENDATIONS (Widget 5)                           │
└─────────────────────────────────────────────────────────┘
```

**Deliverable:** Fully functional client profile with all 5 widgets

---

### Phase 2.5: Create New Client Flow (3 hours)

**File:** `/frontend/app/clients/new/page.tsx`

**Form Fields:**
- Full Name (required)
- Preferred Name
- Birthday (date picker)
- Timezone (select dropdown)
- Contact Methods:
  - Slack User ID
  - Email
  - Phone
  - SMS
- Communication Preferences
- Initial notes

**Features:**
- Form validation with react-hook-form + zod
- Create person + comm_identities in single transaction
- Success redirect to new client profile
- Error handling

**Deliverable:** Working client creation form

---

### Phase 2.6: Add/Edit Important Date Modal (4-5 hours)

**Component:** `/frontend/components/forms/DateItemForm.tsx`

**Features:**
- Title input
- Category select (with icons)
- Date picker
- Recurrence options (None, Yearly, Monthly)
- Notes textarea
- **Reminder Schedule Builder:**
  - Add multiple reminders
  - Select: X days before OR specific datetime
  - Select channel (Slack, Email)
  - Preview: "Will remind on March 1, 2026 at 9:00 AM"
  - Remove reminder button
  - [+ Add Another Reminder] button

**Modal Modes:**
- Create new (from client profile)
- Edit existing (loads data, updates)

**Example UI:**
```
┌─────────────────────────────────────────────────────────┐
│ Add Important Date for Sarah Chen              [Close X]│
├─────────────────────────────────────────────────────────┤
│ Title: [John's Birthday____________]                    │
│                                                         │
│ Category: [🎂 Birthday ▼]                               │
│                                                         │
│ Date: [03/15/2026]  □ Yearly  □ Monthly  ● None       │
│                                                         │
│ Notes:                                                  │
│ [He loves surprise parties___________]                 │
│                                                         │
│ ─── Reminder Schedule ───────────────────────────────  │
│                                                         │
│ Reminder 1:                                             │
│ [14 days before ▼]  [Slack ▼]            [Remove]     │
│ Will remind on March 1, 2026                           │
│                                                         │
│ Reminder 2:                                             │
│ [1 day before ▼]    [Slack ▼]            [Remove]     │
│ Will remind on March 14, 2026                          │
│                                                         │
│ [+ Add Another Reminder]                                │
│                                                         │
│                    [Cancel]  [Save Date & Reminders]   │
└─────────────────────────────────────────────────────────┘
```

**Deliverable:** Reusable date item form component with reminder builder

---

### Phase 2.7: Additional Pages (Optional - 6-8 hours)

#### Important Dates List Page
**File:** `/frontend/app/clients/[id]/dates/page.tsx`
- Full list of all dates for client
- Group by category
- Filter: All / Upcoming / Past
- Show delivery history for each reminder

#### Conversations Page
**File:** `/frontend/app/clients/[id]/conversations/page.tsx`
- Full conversation history
- Message threading
- Filter by channel, date range

#### Project Detail Page
**File:** `/frontend/app/clients/[id]/projects/[projectId]/page.tsx`
- Project info + description
- Task list with checkboxes
- Add/edit/complete tasks
- Link to related date_items

#### Calendar View
**File:** `/frontend/app/calendar/page.tsx`
- Month/week view
- Show all dates across all clients
- Color-coded by category
- Click date → see all events

---

## Testing & Validation

### Unit Tests (Optional - 4-6 hours)

**Backend:**
```bash
pip install pytest pytest-asyncio httpx

# Create tests/
pytest tests/test_date_items_api.py
pytest tests/test_reminders_api.py
pytest tests/test_dashboard_api.py
```

**Frontend:**
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom jest

# Create __tests__/
npm test
```

### Integration Tests (2-3 hours)

**End-to-End Scenarios:**
1. Create client → Add date → Create reminders → Verify dashboard shows upcoming
2. Create project → Add tasks → Mark complete → Verify widget updates
3. Send message via Slack → Verify appears in conversations widget

### Manual Testing Checklist (3-4 hours)

- [ ] Create new client
- [ ] View client profile (all 5 widgets load)
- [ ] Add important date with 2 reminders
- [ ] Edit existing date
- [ ] Delete date (confirms deletion)
- [ ] Create project
- [ ] Add tasks to project
- [ ] View conversations
- [ ] Test search/filter in client directory
- [ ] Test responsive design (mobile view)
- [ ] Test error handling (network failure, 404s)

---

## Performance Optimization

### Backend Optimization (Completed)
- ✅ Database indexes
- ⏳ Query pagination
- ⏳ Response caching (Redis)

### Frontend Optimization (2-3 hours)

#### Code Splitting
```typescript
// Lazy load heavy components
const DateItemForm = dynamic(() => import('@/components/forms/DateItemForm'), {
  loading: () => <Spinner />,
  ssr: false
})
```

#### Data Fetching Strategy
- Use React Query or SWR for caching
- Implement optimistic updates
- Prefetch dashboard data on hover

#### Image Optimization
- Use Next.js Image component
- Lazy load images below fold

---

## Deployment & DevOps

### Backend Deployment (Railway)

**Already configured** - Backend is deployed on Railway

**Checklist:**
- [ ] Environment variables set
- [ ] Database migrations run
- [ ] Health check endpoint working
- [ ] Slack integration active
- [ ] Background workers running

### Frontend Deployment (Vercel)

**Steps:**
1. Connect GitHub repo to Vercel
2. Set environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
   ```
3. Deploy
4. Test production build

### Database Migrations

**Process:**
1. Create migration file in `/database/migrations/`
2. Test locally
3. Apply to production (via Supabase dashboard or CLI)
4. Verify indexes created

---

## Timeline & Milestones

### Week 1: Backend Completion ✅
- [x] Day 1-2: Audit existing APIs
- [x] Day 3-4: Build missing APIs (date-items, reminders, categories, dashboard)
- [x] Day 5: Fix bugs, test endpoints

### Week 2: Frontend Foundation
- [ ] Day 1: Project setup, install dependencies, create UI components
- [ ] Day 2: Extend API client, create widget components
- [ ] Day 3-4: Enhanced dashboard home
- [ ] Day 5: Clients directory

### Week 3: Core Features
- [ ] Day 1-3: Comprehensive client profile (5 widgets)
- [ ] Day 4: Create new client flow
- [ ] Day 5: Add/edit date modal with reminder builder

### Week 4: Polish & Testing
- [ ] Day 1-2: Additional pages (dates list, conversations, projects)
- [ ] Day 3: Testing (manual + integration)
- [ ] Day 4: Bug fixes, performance optimization
- [ ] Day 5: Deployment, documentation

**Total Timeline: 4 weeks to full MVP**

---

## Success Criteria

### Backend (Phase 1) ✅
- [x] All API endpoints implemented
- [x] Date items CRUD working
- [x] Reminders CRUD working
- [x] Dashboard aggregation working
- [x] Categories seeded

### Frontend (Phase 2)
- [ ] Dashboard home shows clients needing attention
- [ ] Client directory searchable/filterable
- [ ] Client profile shows all 5 widgets with real data
- [ ] Can create new client
- [ ] Can add/edit important dates with reminders
- [ ] All pages responsive (mobile/tablet/desktop)

### System (Phase 3)
- [ ] Reminder worker sends Slack notifications correctly
- [ ] Dashboard loads in < 2 seconds
- [ ] No console errors
- [ ] Works in Chrome, Firefox, Safari
- [ ] Deployed to production

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API performance issues | High | Implement caching, pagination, indexes |
| Slack integration breaks | High | Add error handling, retry logic, fallback to email |
| Frontend state management complexity | Medium | Use React Query for server state, Zustand for client state |
| Responsive design challenges | Medium | Mobile-first approach, test early and often |

### Timeline Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | High | Stick to MVP, defer nice-to-haves to Phase 4 |
| Underestimated complexity | Medium | Build in 20% buffer time |
| Dependencies unavailable | Low | Use stable, well-maintained libraries |

---

## Phase 4: Future Enhancements (Post-MVP)

### User Self-Service Portal
- Users can view their own profile
- Users can add their own important dates
- Side panel UI for dates (as designed)

### Advanced Features
- Calendar sync (Google Calendar, Outlook)
- Bulk operations (import dates from CSV)
- Custom reminder templates by category
- Email digest (daily summary for staff)
- Mobile app (React Native)
- Analytics dashboard (reminder effectiveness)
- AI insights (suggest dates based on conversations)

### Security & Compliance
- JWT authentication enforcement
- Role-based access control
- Audit logging
- GDPR compliance features
- SOC 2 compliance

---

## Appendix

### Useful Commands

```bash
# Backend
cd /home/runner/workspace/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd /home/runner/workspace/frontend
npm run dev

# Database
psql "$DATABASE_URL"

# API Testing
curl http://localhost:8000/health
```

### Key Files Reference

**Backend:**
- `/backend/app/api/date_items.py` - Date items API
- `/backend/app/api/reminders.py` - Reminders API
- `/backend/app/api/dashboard.py` - Dashboard aggregation
- `/backend/app/agents/reminder.py` - Reminder generation agent
- `/backend/app/workers/reminder_worker.py` - Background reminder sender

**Frontend:**
- `/frontend/app/page.tsx` - Dashboard home
- `/frontend/app/clients/page.tsx` - Client directory
- `/frontend/app/clients/[id]/page.tsx` - Client profile
- `/frontend/lib/api.ts` - API client
- `/frontend/components/widgets/` - Dashboard widgets

**Documentation:**
- `/BACKEND_SUMMARY.md` - This file
- `/IMPLEMENTATION_PLAN.md` - This file
- `/PROJECT_SUMMARY.md` - Original project overview
- `/database/schema_mvp.sql` - Database schema

---

**Status:** Backend Complete ✅ | Frontend In Progress 🚧
**Last Updated:** October 27, 2025
**Next Action:** Begin Frontend Phase 2.1 - Project Setup
