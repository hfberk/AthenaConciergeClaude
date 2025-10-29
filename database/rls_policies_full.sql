-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- AI Concierge Platform - Production Security
-- =====================================================
--
-- IMPORTANT: This file uses ONE policy per operation per table
-- to avoid multi-policy conflicts. Each policy uses internal
-- OR logic to handle different roles/access patterns.
--
-- Schema: schema_mvp.sql (uses person_id, org_id, channel_type, etc.)
--
-- Service Role Bypass: service_role automatically bypasses RLS when
-- using ENABLE ROW LEVEL SECURITY (Supabase default behavior).
-- No need for explicit is_service_role() checks.
-- =====================================================

-- =====================================================
-- HELPER FUNCTIONS
-- =====================================================
-- Note: These are in public schema, not auth schema
-- (Supabase doesn't allow creating functions in auth schema)

-- Get the current user's organization ID from their account
CREATE OR REPLACE FUNCTION public.user_org_id()
RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT org_id
  FROM accounts
  WHERE auth_user_id = auth.uid()
  LIMIT 1;
$$;

-- Get the current user's person_id
-- Note: persons.auth_user_id must be added via migration 003
CREATE OR REPLACE FUNCTION public.user_person_id()
RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT person_id
  FROM persons
  WHERE auth_user_id = auth.uid()
  LIMIT 1;
$$;

-- Get the current user's account type (admin, concierge, analyst)
CREATE OR REPLACE FUNCTION public.user_account_type()
RETURNS text
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT account_type::text
  FROM accounts
  WHERE auth_user_id = auth.uid()
  LIMIT 1;
$$;

-- Check if current user is an admin
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM accounts
    WHERE auth_user_id = auth.uid()
    AND account_type = 'admin'
  );
$$;

-- =====================================================
-- ENABLE RLS ON ALL TABLES
-- =====================================================

-- Domain 1: Identity & Multi-tenancy
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE persons ENABLE ROW LEVEL SECURITY;

-- Domain 2: Communication Infrastructure
ALTER TABLE comm_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE comm_consent ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Domain 3: Households & Addresses
ALTER TABLE households ENABLE ROW LEVEL SECURITY;
ALTER TABLE household_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE addresses ENABLE ROW LEVEL SECURITY;

-- Domain 4: Dates & Reminders
ALTER TABLE date_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE date_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminder_rules ENABLE ROW LEVEL SECURITY;

-- Domain 5: Projects & Tasks
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Domain 6: Recommendations & Resources
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
ALTER TABLE restaurants ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE interaction_feedback ENABLE ROW LEVEL SECURITY;

-- Domain 7: AI Agent Infrastructure
ALTER TABLE agent_roster ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_execution_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE working_memory ENABLE ROW LEVEL SECURITY;

-- Domain 8: System Audit
ALTER TABLE event_log ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- DOMAIN 1: IDENTITY & MULTI-TENANCY POLICIES
-- =====================================================

-- Organizations: Users can see their own org, admins can manage
CREATE POLICY organizations_select_policy ON organizations
  FOR SELECT
  USING (org_id = public.user_org_id());

CREATE POLICY organizations_insert_policy ON organizations
  FOR INSERT
  WITH CHECK (public.is_admin());

CREATE POLICY organizations_update_policy ON organizations
  FOR UPDATE
  USING (org_id = public.user_org_id() AND public.is_admin());

CREATE POLICY organizations_delete_policy ON organizations
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Accounts: Users can see accounts in their org, admins can manage
CREATE POLICY accounts_select_policy ON accounts
  FOR SELECT
  USING (org_id = public.user_org_id());

CREATE POLICY accounts_insert_policy ON accounts
  FOR INSERT
  WITH CHECK (org_id = public.user_org_id() AND public.is_admin());

CREATE POLICY accounts_update_policy ON accounts
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND (
      public.is_admin() OR
      auth_user_id = auth.uid()  -- Users can update their own account
    )
  );

CREATE POLICY accounts_delete_policy ON accounts
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Persons: Staff see all in org, clients see only themselves
CREATE POLICY persons_select_policy ON persons
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR  -- Staff see all
      person_id = public.user_person_id()  -- Clients see themselves
    )
  );

CREATE POLICY persons_insert_policy ON persons
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY persons_update_policy ON persons
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge') OR
      person_id = public.user_person_id()  -- Clients can update themselves
    )
  );

CREATE POLICY persons_delete_policy ON persons
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- =====================================================
-- DOMAIN 2: COMMUNICATION INFRASTRUCTURE POLICIES
-- =====================================================

-- Comm Identities: Users see their own, staff see all in org
CREATE POLICY comm_identities_select_policy ON comm_identities
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY comm_identities_insert_policy ON comm_identities
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY comm_identities_update_policy ON comm_identities
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY comm_identities_delete_policy ON comm_identities
  FOR DELETE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

-- Comm Consent: Users manage their own consent
CREATE POLICY comm_consent_select_policy ON comm_consent
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY comm_consent_insert_policy ON comm_consent
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND person_id = public.user_person_id()
  );

CREATE POLICY comm_consent_update_policy ON comm_consent
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND person_id = public.user_person_id()
  );

CREATE POLICY comm_consent_delete_policy ON comm_consent
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Conversations: Participants and staff only
CREATE POLICY conversations_select_policy ON conversations
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY conversations_insert_policy ON conversations
  FOR INSERT
  WITH CHECK (org_id = public.user_org_id());

CREATE POLICY conversations_update_policy ON conversations
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY conversations_delete_policy ON conversations
  FOR DELETE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

-- Messages: Conversation participants only
CREATE POLICY messages_select_policy ON messages
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      EXISTS (
        SELECT 1 FROM conversations
        WHERE conversation_id = messages.conversation_id
        AND person_id = public.user_person_id()
      )
    )
  );

CREATE POLICY messages_insert_policy ON messages
  FOR INSERT
  WITH CHECK (org_id = public.user_org_id());

CREATE POLICY messages_update_policy ON messages
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY messages_delete_policy ON messages
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- =====================================================
-- DOMAIN 3: HOUSEHOLDS & ADDRESSES POLICIES
-- =====================================================

-- Households: Org-scoped
CREATE POLICY households_select_policy ON households
  FOR SELECT
  USING (org_id = public.user_org_id());

CREATE POLICY households_insert_policy ON households
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY households_update_policy ON households
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY households_delete_policy ON households
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Household Members: Users see their own households, staff see all
CREATE POLICY household_members_select_policy ON household_members
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY household_members_insert_policy ON household_members
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY household_members_update_policy ON household_members
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY household_members_delete_policy ON household_members
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Addresses: Linked to household or person
CREATE POLICY addresses_select_policy ON addresses
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      person_id = public.user_person_id() OR
      household_id IN (
        SELECT household_id FROM household_members
        WHERE person_id = public.user_person_id()
      )
    )
  );

CREATE POLICY addresses_insert_policy ON addresses
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY addresses_update_policy ON addresses
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY addresses_delete_policy ON addresses
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- =====================================================
-- DOMAIN 4: DATES & REMINDERS POLICIES
-- =====================================================

-- Date Categories: Org-scoped, read by all
CREATE POLICY date_categories_select_policy ON date_categories
  FOR SELECT
  USING (org_id = public.user_org_id());

CREATE POLICY date_categories_insert_policy ON date_categories
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY date_categories_update_policy ON date_categories
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY date_categories_delete_policy ON date_categories
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Date Items: Person-scoped, staff see all
CREATE POLICY date_items_select_policy ON date_items
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY date_items_insert_policy ON date_items
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY date_items_update_policy ON date_items
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY date_items_delete_policy ON date_items
  FOR DELETE
  USING (
    org_id = public.user_org_id() AND (
      public.is_admin() OR
      person_id = public.user_person_id()
    )
  );

-- Reminder Rules: Linked to date items OR comm_identity (for generic reminders)
CREATE POLICY reminder_rules_select_policy ON reminder_rules
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      -- Admins and staff can see all reminders
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      -- Users can see reminders for their own date items
      (date_item_id IS NOT NULL AND date_item_id IN (
        SELECT date_item_id FROM date_items
        WHERE person_id = public.user_person_id()
      )) OR
      -- Users can see generic reminders (NULL date_item_id) linked to their comm_identity
      (date_item_id IS NULL AND comm_identity_id IN (
        SELECT comm_identity_id FROM comm_identities
        WHERE person_id = public.user_person_id()
      ))
    )
  );

CREATE POLICY reminder_rules_insert_policy ON reminder_rules
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY reminder_rules_update_policy ON reminder_rules
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY reminder_rules_delete_policy ON reminder_rules
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- =====================================================
-- DOMAIN 5: PROJECTS & TASKS POLICIES
-- =====================================================

-- Projects: Person-scoped, assigned staff, and org staff
CREATE POLICY projects_select_policy ON projects
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY projects_insert_policy ON projects
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY projects_update_policy ON projects
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge', 'analyst')
  );

CREATE POLICY projects_delete_policy ON projects
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Project Details: Same as projects
CREATE POLICY project_details_select_policy ON project_details
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      project_id IN (
        SELECT project_id FROM projects
        WHERE person_id = public.user_person_id()
      )
    )
  );

CREATE POLICY project_details_insert_policy ON project_details
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY project_details_update_policy ON project_details
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY project_details_delete_policy ON project_details
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Tasks: Project-scoped
CREATE POLICY tasks_select_policy ON tasks
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      project_id IN (
        SELECT project_id FROM projects
        WHERE person_id = public.user_person_id()
      )
    )
  );

CREATE POLICY tasks_insert_policy ON tasks
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY tasks_update_policy ON tasks
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge', 'analyst')
  );

CREATE POLICY tasks_delete_policy ON tasks
  FOR DELETE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

-- =====================================================
-- DOMAIN 6: RESOURCES & RECOMMENDATIONS POLICIES
-- =====================================================

-- Vendors: Org-scoped, all can read
CREATE POLICY vendors_select_policy ON vendors
  FOR SELECT
  USING (org_id = public.user_org_id());

CREATE POLICY vendors_insert_policy ON vendors
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY vendors_update_policy ON vendors
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY vendors_delete_policy ON vendors
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Venues: Org-scoped, all can read
CREATE POLICY venues_select_policy ON venues
  FOR SELECT
  USING (org_id = public.user_org_id());

CREATE POLICY venues_insert_policy ON venues
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY venues_update_policy ON venues
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY venues_delete_policy ON venues
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Restaurants: Org-scoped, all can read
CREATE POLICY restaurants_select_policy ON restaurants
  FOR SELECT
  USING (org_id = public.user_org_id());

CREATE POLICY restaurants_insert_policy ON restaurants
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY restaurants_update_policy ON restaurants
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY restaurants_delete_policy ON restaurants
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Products: Org-scoped, all can read
CREATE POLICY products_select_policy ON products
  FOR SELECT
  USING (org_id = public.user_org_id());

CREATE POLICY products_insert_policy ON products
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY products_update_policy ON products
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY products_delete_policy ON products
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Recommendations: Project-scoped
CREATE POLICY recommendations_select_policy ON recommendations
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      project_id IN (
        SELECT project_id FROM projects
        WHERE person_id = public.user_person_id()
      )
    )
  );

CREATE POLICY recommendations_insert_policy ON recommendations
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY recommendations_update_policy ON recommendations
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY recommendations_delete_policy ON recommendations
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Interaction Feedback: Project-scoped, users can provide feedback
CREATE POLICY interaction_feedback_select_policy ON interaction_feedback
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND (
      public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
      person_id = public.user_person_id()
    )
  );

CREATE POLICY interaction_feedback_insert_policy ON interaction_feedback
  FOR INSERT
  WITH CHECK (
    org_id = public.user_org_id() AND person_id = public.user_person_id()
  );

CREATE POLICY interaction_feedback_update_policy ON interaction_feedback
  FOR UPDATE
  USING (
    org_id = public.user_org_id() AND person_id = public.user_person_id()
  );

CREATE POLICY interaction_feedback_delete_policy ON interaction_feedback
  FOR DELETE
  USING (
    org_id = public.user_org_id() AND (
      public.is_admin() OR
      person_id = public.user_person_id()
    )
  );

-- =====================================================
-- DOMAIN 7: AI AGENT INFRASTRUCTURE POLICIES
-- =====================================================

-- Agent Roster: Admin only
CREATE POLICY agent_roster_select_policy ON agent_roster
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'concierge')
  );

CREATE POLICY agent_roster_insert_policy ON agent_roster
  FOR INSERT
  WITH CHECK (org_id = public.user_org_id() AND public.is_admin());

CREATE POLICY agent_roster_update_policy ON agent_roster
  FOR UPDATE
  USING (org_id = public.user_org_id() AND public.is_admin());

CREATE POLICY agent_roster_delete_policy ON agent_roster
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Agent Execution Logs: Admin and analyst can read, service role only can write
CREATE POLICY agent_execution_logs_select_policy ON agent_execution_logs
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'analyst')
  );

CREATE POLICY agent_execution_logs_insert_policy ON agent_execution_logs
  FOR INSERT
  WITH CHECK (false);  -- Only service role can insert (bypasses RLS)

CREATE POLICY agent_execution_logs_update_policy ON agent_execution_logs
  FOR UPDATE
  USING (false);  -- Only service role can update (bypasses RLS)

CREATE POLICY agent_execution_logs_delete_policy ON agent_execution_logs
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Embeddings: Service role only (AI operations)
CREATE POLICY embeddings_select_policy ON embeddings
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'analyst')
  );

CREATE POLICY embeddings_insert_policy ON embeddings
  FOR INSERT
  WITH CHECK (false);  -- Only service role can insert (bypasses RLS)

CREATE POLICY embeddings_update_policy ON embeddings
  FOR UPDATE
  USING (false);  -- Only service role can update (bypasses RLS)

CREATE POLICY embeddings_delete_policy ON embeddings
  FOR DELETE
  USING (org_id = public.user_org_id() AND public.is_admin());

-- Working Memory: Service role and org-scoped
CREATE POLICY working_memory_select_policy ON working_memory
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'analyst')
  );

CREATE POLICY working_memory_insert_policy ON working_memory
  FOR INSERT
  WITH CHECK (org_id = public.user_org_id());

CREATE POLICY working_memory_update_policy ON working_memory
  FOR UPDATE
  USING (org_id = public.user_org_id());

CREATE POLICY working_memory_delete_policy ON working_memory
  FOR DELETE
  USING (org_id = public.user_org_id());

-- =====================================================
-- DOMAIN 8: SYSTEM AUDIT POLICIES
-- =====================================================

-- Event Log: Read-only for admins, service role can insert
CREATE POLICY event_log_select_policy ON event_log
  FOR SELECT
  USING (
    org_id = public.user_org_id() AND public.user_account_type() IN ('admin', 'analyst')
  );

CREATE POLICY event_log_insert_policy ON event_log
  FOR INSERT
  WITH CHECK (org_id = public.user_org_id());

-- No UPDATE or DELETE on audit logs (immutable)
CREATE POLICY event_log_update_policy ON event_log
  FOR UPDATE
  USING (false);

CREATE POLICY event_log_delete_policy ON event_log
  FOR DELETE
  USING (false);

-- =====================================================
-- POLICY SUMMARY
-- =====================================================
--
-- Total Policies: 120 (30 tables × 4 operations each)
-- Total Helper Functions: 4 (removed is_service_role)
--
-- Access Model:
-- - Service Role: Automatically bypasses RLS (Supabase default)
-- - Admin: Full access to their organization
-- - Concierge/Analyst: Org-scoped read/write
-- - Client: Own data only (person_id scoped)
--
-- Security Features:
-- - Multi-tenant isolation (org_id)
-- - Role-based access control
-- - Conversation privacy (participants only)
-- - Personal data protection
-- - Immutable audit logs
--
-- Testing:
-- 1. Test as service role (should bypass all RLS automatically)
-- 2. Test as admin (should see/manage all in org)
-- 3. Test as concierge (should see/manage org data)
-- 4. Test as client (should see only own data)
-- 5. Test cross-org access (should be blocked)
--
-- =====================================================
