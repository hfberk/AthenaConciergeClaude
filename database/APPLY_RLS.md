# Applying RLS Policies - Quick Guide (MVP)

Ultra-simple guide to enable RLS for your AI Concierge Platform MVP.

## ⚠️ Important Note

These are **ultra-simple "allow all" policies** for MVP development. They provide **zero security** but satisfy Supabase's RLS requirement and unblock your backend.

When you're ready for real security (web interface for users), use `rls_policies_full.sql` instead.

---

## 🚀 Quick Start (2 Steps)

### Step 1: Apply RLS Policies

Copy the entire contents of `database/rls_policies.sql` and paste it into Supabase SQL Editor, then click "Run".

**What this does:**
- Drops any existing policies and helper functions (cleanup)
- Enables RLS on all 30 tables
- Creates 120 ultra-simple policies (all return `true`)
- Everything gets full access to everything

---

### Step 2: Verify It Worked

Run this in Supabase SQL Editor:

```sql
-- Check policies were created
SELECT COUNT(*) as total_policies
FROM pg_policies
WHERE schemaname = 'public';
```

**Expected:** `120` policies

```sql
-- Check RLS is enabled
SELECT tablename, rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Expected:** All tables should show `rls_enabled = true`

---

## ✅ Test Your Backend

Your Slack integration should work immediately:

1. Send a message in Slack
2. Backend should process it without "permission denied" errors
3. Check backend logs for success

---

## 🔓 What Just Happened?

### Before
- RLS enabled with complex policies
- Policies were blocking service_role incorrectly
- Backend getting "permission denied" errors

### After
- RLS still enabled (required by Supabase)
- Policies now allow everything: `USING (true)`
- Backend works without restrictions
- Future web users also have full access (for now)

### Example Policy
```sql
-- Ultra-simple: no restrictions
CREATE POLICY comm_identities_select_policy ON comm_identities
  FOR SELECT
  USING (true);  -- Allow everything
```

---

## 🚨 Security Status

**Current Security Level:** ⚠️ NONE

**Who Can Access Data:**
- ✅ Backend (service_role) - Full access
- ✅ Anyone with anon key - Full access
- ✅ Any authenticated user - Full access

**This is OK for MVP because:**
- You don't have web users yet
- Only your backend accesses the database
- You can add real security later

---

## 🔐 Upgrading to Real Security (Later)

When you build your web interface for staff/clients, follow these steps:

### Step 1: Review Full Policies
```bash
# See the comprehensive RLS policies
cat database/rls_policies_full.sql
```

### Step 2: Understand the Security Model

**Full policies provide:**
- Multi-tenant isolation (org_id)
- Role-based access (admin, concierge, analyst, client)
- Client privacy (clients only see their own data)
- Staff access (staff see all data in their org)

### Step 3: Apply Full Policies

When ready, run `rls_policies_full.sql` in Supabase SQL Editor.

It will:
- Create 4 helper functions
- Replace simple policies with secure ones
- Enable proper multi-tenant security

### Step 4: Test All User Roles

```sql
-- Test as admin (should see all in org)
-- Test as concierge (should see all in org)
-- Test as analyst (should see all in org, limited writes)
-- Test as client (should only see own data)
```

---

## 🐛 Troubleshooting

### Backend Still Not Working?

**1. Check if policies exist:**
```sql
SELECT tablename, COUNT(*) as policies
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;
```
Each table should have exactly 4 policies.

**2. Check if RLS is enabled:**
```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
WHERE rowsecurity = false;
```
Should return 0 rows (all tables should have RLS enabled).

**3. Verify backend is using service_role key:**
```bash
# Check your .env file
grep SUPABASE_SERVICE_KEY backend/.env
```
Should show a JWT token (long string starting with "eyJ...").

**4. Re-run the SQL file:**
The file is idempotent - it drops old policies first, then creates new ones. Safe to run multiple times.

---

## 📋 Rollback Plan

If you need to disable RLS completely:

```sql
-- Disable RLS on all tables
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', t);
    END LOOP;
END $$;
```

**Note:** This will cause errors if you have web users accessing the database. Only use for emergency debugging.

---

## 📚 File Structure

```
database/
├── rls_policies.sql              # Current: Ultra-simple (MVP)
├── rls_policies_full.sql         # Future: Full security
├── schema_mvp.sql                # Database schema
├── RLS_README.md                 # This guide
├── APPLY_RLS.md                  # Application guide
└── migrations/
    └── 003_add_auth_to_persons.sql  # Auth support for clients
```

---

## ✅ Checklist

**For MVP (Now):**
- [ ] Applied `rls_policies.sql` in Supabase SQL Editor
- [ ] Verified 120 policies created
- [ ] Tested Slack integration - no permission errors
- [ ] Backend working normally

**For Production (Later):**
- [ ] Build web interface for staff/clients
- [ ] Set up Supabase Auth for users
- [ ] Apply `rls_policies_full.sql`
- [ ] Test all user roles
- [ ] Verify cross-org isolation
- [ ] Test client privacy

---

**Status**: ⚠️ MVP - Simple Policies Active

**Next Step**: Run `database/rls_policies.sql` in Supabase SQL Editor

**Last Updated**: 2025-10-23
