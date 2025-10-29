# Row Level Security (RLS) Policies - MVP Version

Ultra-simple RLS policies for MVP development with **zero security restrictions**.

## 🎯 Current Setup (MVP)

- ✅ **120 ultra-simple policies** (all return `true`)
- ✅ **Zero helper functions** (not needed)
- ✅ **No security restrictions** (everything allowed)
- ✅ **Satisfies Supabase RLS requirement**
- ⚠️ **No production security** (by design for MVP)

## 📋 Quick Start

### Apply Simple Policies

**Step 1: Apply RLS Policies**
```sql
-- In Supabase SQL Editor, run:
-- File: database/rls_policies.sql
```

This will:
- Drop any existing policies and helper functions
- Enable RLS on all 30 tables
- Create 120 "allow all" policies

**Step 2: Verify**
```sql
-- Check policies were created
SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public';
-- Expected: 120
```

**Step 3: Test Backend**
- Your Slack integration should work immediately
- No more permission errors
- Everything has full access

---

## 🔓 How It Works

Each table has 4 simple policies:

```sql
-- Example: persons table
CREATE POLICY persons_select_policy ON persons FOR SELECT USING (true);
CREATE POLICY persons_insert_policy ON persons FOR INSERT WITH CHECK (true);
CREATE POLICY persons_update_policy ON persons FOR UPDATE USING (true);
CREATE POLICY persons_delete_policy ON persons FOR DELETE USING (true);
```

**Result:** Anyone can do anything. No restrictions.

---

## ⚠️ Security Warning

**IMPORTANT:** These policies provide **ZERO security**. They exist only because:
1. Supabase requires RLS policies when RLS is enabled
2. You need your backend to work NOW
3. Real security can wait until you have web users

### Who Can Access Data?

- ✅ **Backend (service_role):** Full access to everything
- ✅ **Future web users:** Also full access (until you upgrade)
- ✅ **Anyone with anon key:** Full access

---

## 🚀 Upgrading to Real Security

When you're ready to add your web interface for staff/clients:

### Step 1: Review Full Security Policies
```bash
# See the full RLS policies with proper security
cat database/rls_policies_full.sql
```

This file has:
- 4 helper functions for org-based access
- 120 policies with role-based restrictions
- Multi-tenant isolation (org_id)
- Client privacy (person_id)

### Step 2: Apply Full Policies
```sql
-- In Supabase SQL Editor, run:
-- File: database/rls_policies_full.sql
```

### Step 3: Test with Users
- Ensure staff can see their org's data
- Ensure clients can only see their own data
- Verify cross-org isolation works

---

## 📊 Policy Structure

### Current (MVP - Simple)
```sql
-- All policies just return true
USING (true)
WITH CHECK (true)
```

### Future (Production - Secure)
```sql
-- Policies check org membership and roles
USING (
  org_id = public.user_org_id() AND (
    public.user_account_type() IN ('admin', 'concierge', 'analyst') OR
    person_id = public.user_person_id()
  )
)
```

---

## 🐛 Troubleshooting

### Backend Still Getting Permission Errors?

1. **Verify policies exist:**
```sql
SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public';
-- Should return 120
```

2. **Verify RLS is enabled:**
```sql
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';
-- All should show rowsecurity = true
```

3. **Check if old policies are still there:**
```sql
SELECT DISTINCT policyname FROM pg_policies WHERE schemaname = 'public' LIMIT 10;
-- Should see simple names like "persons_select_policy"
```

4. **If problems persist, re-run the SQL file:**
```sql
-- It drops all old policies first, then creates new ones
```

---

## 📚 Files Reference

- `rls_policies.sql` - Current ultra-simple policies (MVP)
- `rls_policies_full.sql` - Full security policies (for later)
- `schema_mvp.sql` - Database schema
- `migrations/003_add_auth_to_persons.sql` - Adds auth support for clients

---

## ✅ Production Readiness Checklist

**Current MVP Status:**
- [x] RLS enabled on all tables
- [x] Policies satisfy Supabase requirements
- [x] Backend works without errors
- [ ] Real security implemented
- [ ] Multi-tenant isolation
- [ ] Role-based access control
- [ ] Web interface authentication

**Before Going to Production:**
1. Replace `rls_policies.sql` with `rls_policies_full.sql`
2. Test all user roles (admin, concierge, analyst, client)
3. Verify cross-org isolation
4. Add audit logging
5. Review and test all access patterns

---

**Status**: ⚠️ MVP Only - No Security

**Last Updated**: 2025-10-23

**Schema Version**: schema_mvp.sql v2.0
