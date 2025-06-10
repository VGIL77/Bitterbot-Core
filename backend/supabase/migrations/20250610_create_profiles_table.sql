-- Create profiles table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    user_tier TEXT DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster tier lookups
CREATE INDEX IF NOT EXISTS idx_profiles_user_tier ON public.profiles(user_tier);

-- Create trigger to automatically create profiles for new users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, user_tier)
    VALUES (NEW.id, NEW.email, 'free')
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger if it doesn't exist
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Insert profiles for existing users
INSERT INTO public.profiles (id, email, user_tier)
SELECT id, email, 'free'
FROM auth.users
ON CONFLICT (id) DO NOTHING;

-- Update Victor's tier to creator
UPDATE public.profiles 
SET user_tier = 'creator' 
WHERE id = '6e650c1a-44bf-4ab3-bc49-10e7f6e34264';

-- Add comment explaining tiers
COMMENT ON COLUMN public.profiles.user_tier IS 'User access tier: free, tester, vip, creator, investor';