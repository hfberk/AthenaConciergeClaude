-- ============================================================================
-- MIGRATION: Add deleted_at columns for soft delete support
-- Created: 2025-10-23
-- Purpose: Add deleted_at TIMESTAMPTZ column to all tables that need soft delete
--          This fixes errors where SupabaseQuery.select_active() expects deleted_at
-- ============================================================================

-- Add deleted_at to critical tables (currently causing errors)
ALTER TABLE comm_identities ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE date_items ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE reminder_rules ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE agent_roster ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE household_members ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Add deleted_at to additional tables for consistency
ALTER TABLE comm_consent ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE date_categories ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE interaction_feedback ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE project_details ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- Create indexes for deleted_at columns on high-traffic tables
-- These improve query performance when filtering for active (non-deleted) records
CREATE INDEX IF NOT EXISTS idx_comm_identities_deleted_at ON comm_identities(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_conversations_deleted_at ON conversations(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_messages_deleted_at ON messages(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_date_items_deleted_at ON date_items(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_deleted_at ON tasks(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_reminder_rules_deleted_at ON reminder_rules(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_agent_roster_deleted_at ON agent_roster(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_organizations_deleted_at ON organizations(deleted_at) WHERE deleted_at IS NULL;

-- Note: We use partial indexes (WHERE deleted_at IS NULL) because:
-- 1. They only index active records, saving space
-- 2. 99% of queries filter for active records (deleted_at IS NULL)
-- 3. Deleted records are rarely queried

-- ============================================================================
-- VERIFICATION QUERIES
-- Run these after migration to verify success:
-- ============================================================================
-- SELECT
--   table_name,
--   column_name,
--   data_type
-- FROM information_schema.columns
-- WHERE column_name = 'deleted_at'
--   AND table_schema = 'public'
-- ORDER BY table_name;
