-- Migration: Create engrams table for neuroscience-inspired memory consolidation
-- This is a ROLLBACK-FRIENDLY migration with proper cleanup

BEGIN;

-- Create engrams table if it doesn't exist
CREATE TABLE IF NOT EXISTS engrams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES threads(thread_id) ON DELETE CASCADE,
    content TEXT NOT NULL, -- The summarized engram content
    metadata JSONB DEFAULT '{}', -- Flexible metadata storage
    created_at TIMESTAMPTZ DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    relevance_score FLOAT DEFAULT 1.0,
    surprise_score FLOAT DEFAULT 0.5,
    token_count INTEGER DEFAULT 0,
    message_range JSONB DEFAULT '{}', -- Start/end message IDs
    
    -- Constraints
    CONSTRAINT relevance_score_range CHECK (relevance_score >= 0 AND relevance_score <= 10),
    CONSTRAINT surprise_score_range CHECK (surprise_score >= 0 AND surprise_score <= 1)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_engrams_thread_id ON engrams(thread_id);
CREATE INDEX IF NOT EXISTS idx_engrams_relevance_score ON engrams(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_engrams_last_accessed ON engrams(last_accessed DESC);
CREATE INDEX IF NOT EXISTS idx_engrams_created_at ON engrams(created_at DESC);

-- Enable RLS on engrams table
ALTER TABLE engrams ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see engrams for threads they have access to
CREATE POLICY engrams_select_policy ON engrams
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM threads t
            WHERE t.thread_id = engrams.thread_id
            AND (
                t.account_id IN (
                    SELECT account_id FROM basejump.account_user 
                    WHERE user_id = auth.uid()
                )
            )
        )
    );

-- Only system can insert/update/delete engrams (via service role)
-- This prevents users from tampering with memory consolidations
CREATE POLICY engrams_system_only_write ON engrams
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Create function to auto-update last_accessed on access
CREATE OR REPLACE FUNCTION update_engram_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if access_count changed
    IF NEW.access_count > OLD.access_count THEN
        NEW.last_accessed = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-updating last_accessed
DROP TRIGGER IF EXISTS trigger_engram_last_accessed ON engrams;
CREATE TRIGGER trigger_engram_last_accessed
    BEFORE UPDATE ON engrams
    FOR EACH ROW
    EXECUTE FUNCTION update_engram_last_accessed();

-- Create function for cleaning old engrams (optional, for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_engrams(
    days_threshold INTEGER DEFAULT 30,
    relevance_threshold FLOAT DEFAULT 0.1
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM engrams
    WHERE last_accessed < NOW() - INTERVAL '1 day' * days_threshold
    AND relevance_score < relevance_threshold;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT SELECT ON engrams TO authenticated;
GRANT ALL ON engrams TO service_role;

-- Add comment for documentation
COMMENT ON TABLE engrams IS 'Stores memory consolidations (engrams) for conversations using neuroscience-inspired continuous micro-consolidation approach';
COMMENT ON COLUMN engrams.content IS 'Summarized content of the memory chunk';
COMMENT ON COLUMN engrams.relevance_score IS 'Dynamic score based on access patterns and decay';
COMMENT ON COLUMN engrams.surprise_score IS 'Saliency score based on unexpected/important content';
COMMENT ON COLUMN engrams.message_range IS 'JSON object with start and end message IDs for this engram';

COMMIT;

-- ROLLBACK INSTRUCTIONS:
-- To completely remove this feature, run:
-- DROP TABLE IF EXISTS engrams CASCADE;
-- DROP FUNCTION IF EXISTS update_engram_last_accessed() CASCADE;
-- DROP FUNCTION IF EXISTS cleanup_old_engrams(INTEGER, FLOAT) CASCADE;