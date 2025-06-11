-- SQL script to add three users to creator tier
-- Run this in your Supabase SQL editor

-- Add users to creator tier
INSERT INTO user_tiers (user_id, tier, created_at, updated_at)
VALUES 
  ('3ba994c3-5a1e-409e-84aa-e53c77964de8', 'creator', NOW(), NOW()),
  ('6e8f8ae7-7b5d-4c6e-a3da-afa7536210ce', 'creator', NOW(), NOW()),
  ('ea16f8ab-2bd5-4939-8a9a-5842d94ed380', 'creator', NOW(), NOW())
ON CONFLICT (user_id) 
DO UPDATE SET 
  tier = 'creator',
  updated_at = NOW();

-- Verify the users were added
SELECT user_id, tier, created_at, updated_at 
FROM user_tiers 
WHERE user_id IN (
  '3ba994c3-5a1e-409e-84aa-e53c77964de8',
  '6e8f8ae7-7b5d-4c6e-a3da-afa7536210ce',
  'ea16f8ab-2bd5-4939-8a9a-5842d94ed380'
);