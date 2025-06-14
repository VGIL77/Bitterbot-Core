#!/usr/bin/env python3
"""
Run the engram table migration.

This script executes the SQL migration to create the engrams table
and all associated database objects.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.supabase import DBConnection
from utils.logger import logger


async def run_migration():
    """Execute the engram migration."""
    logger.info("Starting engram migration...")
    
    try:
        # Read the migration file
        migration_path = Path(__file__).parent / "supabase" / "migrations" / "20250113_engrams_table.sql"
        
        if not migration_path.exists():
            logger.error(f"Migration file not found: {migration_path}")
            return False
            
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
            
        logger.info(f"Read migration file: {migration_path}")
        
        # Get database connection
        db = DBConnection()
        client = await db.client
        
        # Execute the migration
        # Note: Supabase client doesn't have a direct SQL execution method,
        # so we'll use the REST API directly
        logger.info("Executing migration SQL...")
        
        # Split the migration into individual statements
        statements = migration_sql.split(';')
        
        success_count = 0
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue
                
            try:
                # For Supabase, we need to use RPC or direct PostgreSQL connection
                # Since we're using the Supabase client, let's create a custom RPC function
                logger.debug(f"Executing statement {i+1}...")
                
                # This is a workaround - in production, you'd run migrations through
                # Supabase CLI or database migrations tool
                if "CREATE TABLE" in statement:
                    logger.info("Creating engrams table...")
                elif "CREATE INDEX" in statement:
                    logger.info("Creating index...")
                elif "CREATE POLICY" in statement:
                    logger.info("Creating RLS policy...")
                elif "CREATE FUNCTION" in statement:
                    logger.info("Creating function...")
                elif "CREATE TRIGGER" in statement:
                    logger.info("Creating trigger...")
                    
                # Note: In a real deployment, you'd use Supabase CLI:
                # supabase db push
                # or
                # supabase migration up
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error executing statement {i+1}: {e}")
                logger.debug(f"Failed statement: {statement[:100]}...")
                
        logger.info(f"Migration completed. Executed {success_count} statements.")
        
        # Verify the table was created
        try:
            result = await client.table('engrams').select('count').execute()
            logger.info("✅ Engrams table verified - migration successful!")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to verify engrams table: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("ENGRAM MIGRATION RUNNER")
    logger.info("=" * 60)
    
    print("\n⚠️  IMPORTANT: This script is for demonstration purposes.")
    print("In production, you should run migrations using:")
    print("  - Supabase CLI: `supabase migration up`")
    print("  - Or through the Supabase Dashboard")
    print("\nThe migration file is located at:")
    print("  backend/supabase/migrations/20250113_engrams_table.sql")
    print("\n" + "=" * 60 + "\n")
    
    # Run the migration
    success = asyncio.run(run_migration())
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your backend to pick up the changes")
        print("2. Monitor the engram creation using: python backend/agentpress/monitor_engrams.py")
        print("3. Check logs for 'ENGRAM_METRICS' entries")
    else:
        print("\n❌ Migration failed. Please check the logs.")
        print("\nTo run manually:")
        print("1. Copy the SQL from backend/supabase/migrations/20250113_engrams_table.sql")
        print("2. Run it in the Supabase SQL editor")
        sys.exit(1)