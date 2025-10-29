-- =====================================================
-- ULTRA-SIMPLE RLS POLICIES
-- AI Concierge Platform - MVP (No Security Restrictions)
-- =====================================================
--
-- IMPORTANT: These policies allow ALL access to ALL data.
-- This is intentionally simple for MVP development.
-- Replace with rls_policies_full.sql when you need real security.
--
-- Why this exists:
-- - Supabase requires RLS policies when RLS is enabled
-- - These policies satisfy that requirement
-- - But they don't actually restrict anything (all return true)
--
-- Schema: schema_mvp.sql
-- =====================================================

-- =====================================================
-- CLEANUP: Drop existing policies and functions
-- =====================================================

-- Drop all existing policies
DO $$
DECLARE
    p record;
BEGIN
    FOR p IN
        SELECT schemaname, tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', p.policyname, p.tablename);
    END LOOP;
END $$;

-- Drop all helper functions (we don't need any for simple policies)
DROP FUNCTION IF EXISTS public.user_org_id();
DROP FUNCTION IF EXISTS public.user_person_id();
DROP FUNCTION IF EXISTS public.user_account_type();
DROP FUNCTION IF EXISTS public.is_admin();

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
-- ULTRA-SIMPLE POLICIES: Allow Everything
-- =====================================================
-- Pattern: Each table gets 4 policies that all return true
-- This satisfies Supabase's RLS requirement without restricting access

-- Domain 1: Identity & Multi-tenancy
CREATE POLICY organizations_select_policy ON organizations FOR SELECT USING (true);
CREATE POLICY organizations_insert_policy ON organizations FOR INSERT WITH CHECK (true);
CREATE POLICY organizations_update_policy ON organizations FOR UPDATE USING (true);
CREATE POLICY organizations_delete_policy ON organizations FOR DELETE USING (true);

CREATE POLICY accounts_select_policy ON accounts FOR SELECT USING (true);
CREATE POLICY accounts_insert_policy ON accounts FOR INSERT WITH CHECK (true);
CREATE POLICY accounts_update_policy ON accounts FOR UPDATE USING (true);
CREATE POLICY accounts_delete_policy ON accounts FOR DELETE USING (true);

CREATE POLICY persons_select_policy ON persons FOR SELECT USING (true);
CREATE POLICY persons_insert_policy ON persons FOR INSERT WITH CHECK (true);
CREATE POLICY persons_update_policy ON persons FOR UPDATE USING (true);
CREATE POLICY persons_delete_policy ON persons FOR DELETE USING (true);

-- Domain 2: Communication Infrastructure
CREATE POLICY comm_identities_select_policy ON comm_identities FOR SELECT USING (true);
CREATE POLICY comm_identities_insert_policy ON comm_identities FOR INSERT WITH CHECK (true);
CREATE POLICY comm_identities_update_policy ON comm_identities FOR UPDATE USING (true);
CREATE POLICY comm_identities_delete_policy ON comm_identities FOR DELETE USING (true);

CREATE POLICY comm_consent_select_policy ON comm_consent FOR SELECT USING (true);
CREATE POLICY comm_consent_insert_policy ON comm_consent FOR INSERT WITH CHECK (true);
CREATE POLICY comm_consent_update_policy ON comm_consent FOR UPDATE USING (true);
CREATE POLICY comm_consent_delete_policy ON comm_consent FOR DELETE USING (true);

CREATE POLICY conversations_select_policy ON conversations FOR SELECT USING (true);
CREATE POLICY conversations_insert_policy ON conversations FOR INSERT WITH CHECK (true);
CREATE POLICY conversations_update_policy ON conversations FOR UPDATE USING (true);
CREATE POLICY conversations_delete_policy ON conversations FOR DELETE USING (true);

CREATE POLICY messages_select_policy ON messages FOR SELECT USING (true);
CREATE POLICY messages_insert_policy ON messages FOR INSERT WITH CHECK (true);
CREATE POLICY messages_update_policy ON messages FOR UPDATE USING (true);
CREATE POLICY messages_delete_policy ON messages FOR DELETE USING (true);

-- Domain 3: Households & Addresses
CREATE POLICY households_select_policy ON households FOR SELECT USING (true);
CREATE POLICY households_insert_policy ON households FOR INSERT WITH CHECK (true);
CREATE POLICY households_update_policy ON households FOR UPDATE USING (true);
CREATE POLICY households_delete_policy ON households FOR DELETE USING (true);

CREATE POLICY household_members_select_policy ON household_members FOR SELECT USING (true);
CREATE POLICY household_members_insert_policy ON household_members FOR INSERT WITH CHECK (true);
CREATE POLICY household_members_update_policy ON household_members FOR UPDATE USING (true);
CREATE POLICY household_members_delete_policy ON household_members FOR DELETE USING (true);

CREATE POLICY addresses_select_policy ON addresses FOR SELECT USING (true);
CREATE POLICY addresses_insert_policy ON addresses FOR INSERT WITH CHECK (true);
CREATE POLICY addresses_update_policy ON addresses FOR UPDATE USING (true);
CREATE POLICY addresses_delete_policy ON addresses FOR DELETE USING (true);

-- Domain 4: Dates & Reminders
CREATE POLICY date_categories_select_policy ON date_categories FOR SELECT USING (true);
CREATE POLICY date_categories_insert_policy ON date_categories FOR INSERT WITH CHECK (true);
CREATE POLICY date_categories_update_policy ON date_categories FOR UPDATE USING (true);
CREATE POLICY date_categories_delete_policy ON date_categories FOR DELETE USING (true);

CREATE POLICY date_items_select_policy ON date_items FOR SELECT USING (true);
CREATE POLICY date_items_insert_policy ON date_items FOR INSERT WITH CHECK (true);
CREATE POLICY date_items_update_policy ON date_items FOR UPDATE USING (true);
CREATE POLICY date_items_delete_policy ON date_items FOR DELETE USING (true);

CREATE POLICY reminder_rules_select_policy ON reminder_rules FOR SELECT USING (true);
CREATE POLICY reminder_rules_insert_policy ON reminder_rules FOR INSERT WITH CHECK (true);
CREATE POLICY reminder_rules_update_policy ON reminder_rules FOR UPDATE USING (true);
CREATE POLICY reminder_rules_delete_policy ON reminder_rules FOR DELETE USING (true);

-- Domain 5: Projects & Tasks
CREATE POLICY projects_select_policy ON projects FOR SELECT USING (true);
CREATE POLICY projects_insert_policy ON projects FOR INSERT WITH CHECK (true);
CREATE POLICY projects_update_policy ON projects FOR UPDATE USING (true);
CREATE POLICY projects_delete_policy ON projects FOR DELETE USING (true);

CREATE POLICY project_details_select_policy ON project_details FOR SELECT USING (true);
CREATE POLICY project_details_insert_policy ON project_details FOR INSERT WITH CHECK (true);
CREATE POLICY project_details_update_policy ON project_details FOR UPDATE USING (true);
CREATE POLICY project_details_delete_policy ON project_details FOR DELETE USING (true);

CREATE POLICY tasks_select_policy ON tasks FOR SELECT USING (true);
CREATE POLICY tasks_insert_policy ON tasks FOR INSERT WITH CHECK (true);
CREATE POLICY tasks_update_policy ON tasks FOR UPDATE USING (true);
CREATE POLICY tasks_delete_policy ON tasks FOR DELETE USING (true);

-- Domain 6: Recommendations & Resources
CREATE POLICY vendors_select_policy ON vendors FOR SELECT USING (true);
CREATE POLICY vendors_insert_policy ON vendors FOR INSERT WITH CHECK (true);
CREATE POLICY vendors_update_policy ON vendors FOR UPDATE USING (true);
CREATE POLICY vendors_delete_policy ON vendors FOR DELETE USING (true);

CREATE POLICY venues_select_policy ON venues FOR SELECT USING (true);
CREATE POLICY venues_insert_policy ON venues FOR INSERT WITH CHECK (true);
CREATE POLICY venues_update_policy ON venues FOR UPDATE USING (true);
CREATE POLICY venues_delete_policy ON venues FOR DELETE USING (true);

CREATE POLICY restaurants_select_policy ON restaurants FOR SELECT USING (true);
CREATE POLICY restaurants_insert_policy ON restaurants FOR INSERT WITH CHECK (true);
CREATE POLICY restaurants_update_policy ON restaurants FOR UPDATE USING (true);
CREATE POLICY restaurants_delete_policy ON restaurants FOR DELETE USING (true);

CREATE POLICY products_select_policy ON products FOR SELECT USING (true);
CREATE POLICY products_insert_policy ON products FOR INSERT WITH CHECK (true);
CREATE POLICY products_update_policy ON products FOR UPDATE USING (true);
CREATE POLICY products_delete_policy ON products FOR DELETE USING (true);

CREATE POLICY recommendations_select_policy ON recommendations FOR SELECT USING (true);
CREATE POLICY recommendations_insert_policy ON recommendations FOR INSERT WITH CHECK (true);
CREATE POLICY recommendations_update_policy ON recommendations FOR UPDATE USING (true);
CREATE POLICY recommendations_delete_policy ON recommendations FOR DELETE USING (true);

CREATE POLICY interaction_feedback_select_policy ON interaction_feedback FOR SELECT USING (true);
CREATE POLICY interaction_feedback_insert_policy ON interaction_feedback FOR INSERT WITH CHECK (true);
CREATE POLICY interaction_feedback_update_policy ON interaction_feedback FOR UPDATE USING (true);
CREATE POLICY interaction_feedback_delete_policy ON interaction_feedback FOR DELETE USING (true);

-- Domain 7: AI Agent Infrastructure
CREATE POLICY agent_roster_select_policy ON agent_roster FOR SELECT USING (true);
CREATE POLICY agent_roster_insert_policy ON agent_roster FOR INSERT WITH CHECK (true);
CREATE POLICY agent_roster_update_policy ON agent_roster FOR UPDATE USING (true);
CREATE POLICY agent_roster_delete_policy ON agent_roster FOR DELETE USING (true);

CREATE POLICY agent_execution_logs_select_policy ON agent_execution_logs FOR SELECT USING (true);
CREATE POLICY agent_execution_logs_insert_policy ON agent_execution_logs FOR INSERT WITH CHECK (true);
CREATE POLICY agent_execution_logs_update_policy ON agent_execution_logs FOR UPDATE USING (true);
CREATE POLICY agent_execution_logs_delete_policy ON agent_execution_logs FOR DELETE USING (true);

CREATE POLICY embeddings_select_policy ON embeddings FOR SELECT USING (true);
CREATE POLICY embeddings_insert_policy ON embeddings FOR INSERT WITH CHECK (true);
CREATE POLICY embeddings_update_policy ON embeddings FOR UPDATE USING (true);
CREATE POLICY embeddings_delete_policy ON embeddings FOR DELETE USING (true);

CREATE POLICY working_memory_select_policy ON working_memory FOR SELECT USING (true);
CREATE POLICY working_memory_insert_policy ON working_memory FOR INSERT WITH CHECK (true);
CREATE POLICY working_memory_update_policy ON working_memory FOR UPDATE USING (true);
CREATE POLICY working_memory_delete_policy ON working_memory FOR DELETE USING (true);

-- Domain 8: System Audit
CREATE POLICY event_log_select_policy ON event_log FOR SELECT USING (true);
CREATE POLICY event_log_insert_policy ON event_log FOR INSERT WITH CHECK (true);
CREATE POLICY event_log_update_policy ON event_log FOR UPDATE USING (true);
CREATE POLICY event_log_delete_policy ON event_log FOR DELETE USING (true);

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify RLS is enabled on all tables
SELECT tablename, rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
-- Expected: All 30 tables should show rls_enabled = true

-- Verify all policies were created
SELECT COUNT(*) as total_policies
FROM pg_policies
WHERE schemaname = 'public';
-- Expected: 120 policies (30 tables × 4 operations)

-- List all policies
SELECT tablename, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;
-- Expected: Each table should have exactly 4 policies

-- =====================================================
-- POLICY SUMMARY
-- =====================================================
--
-- Total Policies: 120 (30 tables × 4 operations each)
-- Total Helper Functions: 0 (none needed)
--
-- Access Model:
-- - Everyone: Full access to everything (no restrictions)
-- - Backend: Works without any permission issues
-- - Frontend: Will also have full access (until you replace with rls_policies_full.sql)
--
-- Security Level: NONE (intentionally for MVP)
--
-- Next Steps:
-- 1. Apply this file in Supabase SQL Editor
-- 2. Verify backend works (Slack integration, etc.)
-- 3. When ready for real security, replace with rls_policies_full.sql
--
-- =====================================================
