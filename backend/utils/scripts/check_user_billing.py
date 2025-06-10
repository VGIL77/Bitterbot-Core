#!/usr/bin/env python3
"""
Script to check a user's billing status and tier.
Usage: python check_user_billing.py <user_id>
"""
import asyncio
import sys
from typing import Optional
from supabase import create_client
from utils.config import config

async def check_user_billing(user_id: str):
    """Check billing status for a specific user."""
    client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    
    print(f"\n=== Checking billing status for user: {user_id} ===\n")
    
    # Check profile
    try:
        profile = await client.table('profiles').select('*').eq('id', user_id).single()
        if profile.data:
            print(f"Profile found:")
            print(f"  Email: {profile.data.get('email', 'N/A')}")
            print(f"  Tier: {profile.data.get('user_tier', 'N/A')}")
            print(f"  Created: {profile.data.get('created_at', 'N/A')}")
        else:
            print("❌ No profile found for this user")
    except Exception as e:
        print(f"❌ Error checking profile: {e}")
    
    # Check auth user
    try:
        auth_user = await client.auth.admin.get_user_by_id(user_id)
        if auth_user:
            print(f"\nAuth user found:")
            print(f"  Email: {auth_user.user.email}")
            print(f"  Created: {auth_user.user.created_at}")
    except Exception as e:
        print(f"❌ Error checking auth user: {e}")
    
    # Check subscriptions
    try:
        subs = await client.table('subscriptions').select('*').eq('account_id', user_id).execute()
        if subs.data:
            print(f"\nSubscriptions found: {len(subs.data)}")
            for sub in subs.data:
                print(f"  - Status: {sub.get('status')}, Price ID: {sub.get('price_id')}")
        else:
            print("\nNo subscriptions found")
    except Exception as e:
        print(f"❌ Error checking subscriptions: {e}")
    
    # Test billing check
    try:
        from services.billing import check_billing_status
        has_access, message, details = await check_billing_status(user_id)
        print(f"\nBilling check result:")
        print(f"  Has access: {has_access}")
        print(f"  Message: {message}")
        print(f"  Details: {details}")
    except Exception as e:
        print(f"❌ Error running billing check: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_user_billing.py <user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    asyncio.run(check_user_billing(user_id))