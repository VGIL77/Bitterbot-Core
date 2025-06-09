-- Add user tier system for privileged access
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS user_tier TEXT DEFAULT 'free';

-- Create index for faster tier lookups
CREATE INDEX IF NOT EXISTS idx_profiles_user_tier ON public.profiles(user_tier);

-- Set creator tier for Victor
UPDATE public.profiles 
SET user_tier = 'creator' 
WHERE id = '6e650c1a-44bf-4ab3-bc49-10e7f6e34264';

-- Add comment explaining tiers
COMMENT ON COLUMN public.profiles.user_tier IS 'User access tier: free, tester, vip, creator, investor';