-- Create engrams table for neuroscience-inspired memory consolidation
-- This migration is designed to be rollback-friendly

-- Create the engrams table if it doesn't exist
CREATE TABLE IF NOT EXISTS engrams (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Thread association
    thread_id UUID NOT NULL REFERENCES threads(thread_id) ON DELETE CASCADE,
    
    -- Core content
    content TEXT NOT NULL,  -- The consolidated summary
    message_range JSONB NOT NULL DEFAULT '{}',  -- {start: msg_id, end: msg_id, count: N}
    
    -- Token tracking
    token_count INTEGER NOT NULL DEFAULT 0,
    
    -- Relevance and scoring
    relevance_score FLOAT NOT NULL DEFAULT 1.0 CHECK (relevance_score >= 0 AND relevance_score <= 5),
    surprise_score FLOAT NOT NULL DEFAULT 0.5 CHECK (surprise_score >= 0 AND surprise_score <= 1),
    
    -- Usage tracking (Hebbian learning)
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}',  -- {topics: [], trigger: '', has_code: bool, etc.}
    
    -- Soft delete support
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_engrams_thread_id ON engrams(thread_id) WHERE NOT is_deleted;
CREATE INDEX IF NOT EXISTS idx_engrams_relevance ON engrams(thread_id, relevance_score DESC) WHERE NOT is_deleted;
CREATE INDEX IF NOT EXISTS idx_engrams_created_at ON engrams(thread_id, created_at DESC) WHERE NOT is_deleted;
CREATE INDEX IF NOT EXISTS idx_engrams_last_accessed ON engrams(thread_id, last_accessed DESC) WHERE NOT is_deleted;

-- Enable Row Level Security
ALTER TABLE engrams ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see engrams for threads they have access to
CREATE POLICY "Users can view their own engrams" ON engrams
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM threads
            WHERE threads.thread_id = engrams.thread_id
            AND threads.account_id = auth.uid()
        )
    );

-- Only system can insert/update/delete engrams (via service role)
CREATE POLICY "Service role can manage engrams" ON engrams
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_engrams_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER engrams_updated_at
    BEFORE UPDATE ON engrams
    FOR EACH ROW
    EXECUTE FUNCTION update_engrams_updated_at();

-- Add comment for documentation
COMMENT ON TABLE engrams IS 'Neuroscience-inspired memory consolidation system. Stores compressed representations of conversation segments to prevent context window overflow while maintaining long-term coherence.';
COMMENT ON COLUMN engrams.content IS 'The consolidated summary of the message segment';
COMMENT ON COLUMN engrams.relevance_score IS 'Current relevance score with decay applied over time (0-5)';
COMMENT ON COLUMN engrams.surprise_score IS 'Saliency/importance score based on content analysis (0-1)';
COMMENT ON COLUMN engrams.access_count IS 'Number of times this engram has been retrieved (Hebbian learning)';
COMMENT ON COLUMN engrams.metadata IS 'Additional data: topics, trigger type, content flags, etc.';

-- Create a function to get engram statistics for monitoring
CREATE OR REPLACE FUNCTION get_engram_stats(p_thread_id UUID DEFAULT NULL)
RETURNS TABLE (
    total_engrams BIGINT,
    avg_relevance_score FLOAT,
    avg_surprise_score FLOAT,
    total_tokens_compressed BIGINT,
    oldest_engram_age_days INTEGER,
    most_accessed_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_engrams,
        AVG(relevance_score)::FLOAT as avg_relevance_score,
        AVG(surprise_score)::FLOAT as avg_surprise_score,
        SUM(token_count)::BIGINT as total_tokens_compressed,
        EXTRACT(DAYS FROM (NOW() - MIN(created_at)))::INTEGER as oldest_engram_age_days,
        MAX(access_count)::INTEGER as most_accessed_count
    FROM engrams
    WHERE NOT is_deleted
    AND (p_thread_id IS NULL OR thread_id = p_thread_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the stats function
GRANT EXECUTE ON FUNCTION get_engram_stats(UUID) TO authenticated;

-- Create helper function for counting recent engrams (used by dashboard)
CREATE OR REPLACE FUNCTION count_recent_engrams(
    thread_id_param UUID,
    since_time TIMESTAMPTZ
)
RETURNS TABLE(count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(*)::BIGINT
    FROM engrams
    WHERE thread_id = thread_id_param
    AND created_at >= since_time
    AND NOT is_deleted;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION count_recent_engrams(UUID, TIMESTAMPTZ) TO authenticated;

-- Rollback commands (commented out for safety)
-- DROP FUNCTION IF EXISTS count_recent_engrams(UUID, TIMESTAMPTZ);
-- DROP FUNCTION IF EXISTS get_engram_stats(UUID);
-- DROP TRIGGER IF EXISTS engrams_updated_at ON engrams;
-- DROP FUNCTION IF EXISTS update_engrams_updated_at();
-- DROP POLICY IF EXISTS "Service role can manage engrams" ON engrams;
-- DROP POLICY IF EXISTS "Users can view their own engrams" ON engrams;
-- DROP TABLE IF EXISTS engrams;