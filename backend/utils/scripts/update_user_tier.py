#!/usr/bin/env python3
"""
Script to update a user's tier.
Usage: python update_user_tier.py <user_id> <tier>
Valid tiers: free, creator, tester, vip, investor
"""
import asyncio
import sys
from supabase import create_client
from utils.config import config

VALID_TIERS = ['free', 'creator', 'tester', 'vip', 'investor']

async def update_user_tier(user_id: str, tier: str):
    """Update a user's tier."""
    if tier not in VALID_TIERS:
        print(f"❌ Invalid tier: {tier}")
        print(f"Valid tiers: {', '.join(VALID_TIERS)}")
        return
    
    client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    
    print(f"\n=== Updating user tier ===")
    print(f"User ID: {user_id}")
    print(f"New tier: {tier}")
    
    try:
        # Check if profile exists
        profile = await client.table('profiles').select('*').eq('id', user_id).single()
        
        if profile.data:
            # Update existing profile
            result = await client.table('profiles').update({'user_tier': tier}).eq('id', user_id).execute()
            print(f"✅ Updated existing profile to tier: {tier}")
        else:
            # Create new profile
            result = await client.table('profiles').insert({
                'id': user_id,
                'user_tier': tier
            }).execute()
            print(f"✅ Created new profile with tier: {tier}")
        
        # Verify the update
        verify = await client.table('profiles').select('*').eq('id', user_id).single()
        if verify.data:
            print(f"\nVerification:")
            print(f"  User ID: {verify.data.get('id')}")
            print(f"  Tier: {verify.data.get('user_tier')}")
            print(f"  Email: {verify.data.get('email', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error updating tier: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_user_tier.py <user_id> <tier>")
        print(f"Valid tiers: {', '.join(VALID_TIERS)}")
        sys.exit(1)
    
    user_id = sys.argv[1]
    tier = sys.argv[2]
    asyncio.run(update_user_tier(user_id, tier))