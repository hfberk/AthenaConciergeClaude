-- =====================================================
-- Migration 003: Add Authentication Support for Clients
-- Date: 2025-10-23
-- =====================================================
--
-- Purpose: Add auth_user_id to persons table to enable client authentication
--
-- Background:
-- - Currently only staff (accounts table) can authenticate
-- - Clients will need to authenticate for web portal access
-- - This adds the necessary link between Supabase auth and persons records
--
-- =====================================================

-- Add auth_user_id column to persons table
ALTER TABLE persons
  ADD COLUMN auth_user_id UUID REFERENCES auth.users(id);

-- Create index for performance
CREATE INDEX idx_persons_auth_user ON persons(auth_user_id);

-- Add unique constraint (one auth user per person)
ALTER TABLE persons
  ADD CONSTRAINT persons_auth_user_id_key UNIQUE (auth_user_id);

-- Add comment
COMMENT ON COLUMN persons.auth_user_id IS 'Links person to Supabase auth user for client authentication';

-- =====================================================
-- Verification Query
-- =====================================================
-- Run this to verify the migration succeeded:
--
-- SELECT
--   table_name,
--   column_name,
--   data_type,
--   is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'persons'
--   AND column_name = 'auth_user_id';
--
-- Expected result:
-- | table_name | column_name  | data_type | is_nullable |
-- |------------|--------------|-----------|-------------|
-- | persons    | auth_user_id | uuid      | YES         |
--
-- =====================================================

-- =====================================================
-- Usage Notes
-- =====================================================
--
-- Staff Authentication:
--   - Staff continue to use accounts.auth_user_id
--   - RLS checks accounts table first for staff
--
-- Client Authentication:
--   - New clients created via Supabase Auth signup
--   - Link auth_user_id to persons record
--   - RLS checks persons table for client access
--
-- Slack/Email Integrations:
--   - Persons without auth_user_id (NULL) are integration-only
--   - Backend uses service role to access their data
--   - No change to existing integration flow
--
-- =====================================================
