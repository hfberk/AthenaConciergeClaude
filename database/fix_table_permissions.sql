-- =====================================================
-- FIX: Grant Table Permissions to Service Role
-- =====================================================
--
-- Problem: "permission denied for table comm_identities"
-- Even with RLS policies that return true, getting permission errors.
-- This means the service_role doesn't have GRANT permissions on tables.
--
-- Solution: Grant all permissions to service_role and postgres
-- =====================================================

-- Grant all permissions on all tables to service_role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Grant all permissions to postgres role (superuser)
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Also grant to authenticated and anon roles for future web users
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO anon;

-- =====================================================
-- VERIFICATION
-- =====================================================

-- Check what privileges service_role has on comm_identities
SELECT
    grantee,
    privilege_type
FROM information_schema.table_privileges
WHERE table_schema = 'public'
AND table_name = 'comm_identities'
AND grantee IN ('service_role', 'postgres', 'authenticated', 'anon')
ORDER BY grantee, privilege_type;

-- Expected: service_role should have SELECT, INSERT, UPDATE, DELETE, etc.

-- Check all tables
SELECT
    table_name,
    COUNT(*) FILTER (WHERE grantee = 'service_role') as service_role_grants,
    COUNT(*) FILTER (WHERE grantee = 'authenticated') as authenticated_grants
FROM information_schema.table_privileges
WHERE table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;

-- All tables should have multiple grants for service_role
