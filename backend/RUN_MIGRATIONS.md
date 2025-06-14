# Running ENGRAM Migrations

## New Migration Created

We've created 1 new migration for the ENGRAM system:

1. **`20250113_engrams_table.sql`** - Creates the engrams table and related functions

The admin console uses the existing `creator` tier from the profiles table - no additional migration needed!

## Steps to Deploy

### 1. First, Pull Latest Changes
```bash
# Make sure you have the latest from remote
supabase db pull
```

### 2. Review the Migrations
The migrations are designed to be safe and rollback-friendly:
- They use `IF NOT EXISTS` clauses
- They don't modify existing tables destructively
- They include rollback commands (commented out)

### 3. Push the Migrations
```bash
# Push new migrations to Supabase
supabase db push

# Or if you want to see what will be applied first:
supabase db diff
```

### 4. Verify Your Creator Access
You should already have creator tier access. Check with:

```sql
-- Check your tier
SELECT tier FROM profiles 
WHERE account_id = auth.uid();

-- If you need creator access, update your tier:
UPDATE profiles 
SET tier = 'creator'
WHERE account_id = 'your-user-id';
```

### 5. Verify Migration Success
Check that tables were created:

```sql
-- Should return the table structure
SELECT * FROM engrams LIMIT 0;

-- Should show your tier
SELECT tier FROM profiles WHERE account_id = 'your-user-id';
```

## What the Migration Does

### engrams_table.sql
- Creates `engrams` table for memory storage
- Adds indexes for performance
- Sets up RLS policies
- Creates helper functions
- Adds update triggers

The admin console uses the existing `profiles.tier` system where 'creator', 'tester', 'vip', and 'investor' tiers have privileged access.

## Rollback (if needed)

If you need to rollback, the migrations include commented rollback commands at the bottom. Or you can run:

```sql
-- Rollback engrams
DROP TABLE IF EXISTS engrams CASCADE;
DROP FUNCTION IF EXISTS count_recent_engrams(UUID, TIMESTAMPTZ);
DROP FUNCTION IF EXISTS get_engram_stats(UUID);
```

## Important Notes

1. **The engrams table is optional** - BitterBot works fine without it
2. **No existing data is modified** - Only new tables/columns are added
3. **Feature is disabled by default** - Set `ENGRAM_ENABLED=true` to activate
4. **Admin access is required** - Update your user role after migration

The migrations are designed to be non-destructive and can be safely applied to a running system.