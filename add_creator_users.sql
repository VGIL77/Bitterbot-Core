-- Add users to creator tier for testing
-- Replace 'user_id_1' and 'user_id_2' with the actual user IDs

-- First, check if profiles exist and update/insert as needed
INSERT INTO profiles (id, user_tier)
VALUES 
  ('user_id_1', 'creator'),
  ('user_id_2', 'creator')
ON CONFLICT (id) 
DO UPDATE SET user_tier = 'creator';

-- Verify the updates
SELECT id, email, user_tier 
FROM profiles 
WHERE id IN ('user_id_1', 'user_id_2');