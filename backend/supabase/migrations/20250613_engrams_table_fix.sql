-- Migration to fix engrams table schema inconsistency
-- Adds missing columns from the original design

BEGIN;

-- Add is_deleted column if it doesn't exist
ALTER TABLE engrams 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- Add updated_at column if it doesn't exist
ALTER TABLE engrams 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Update existing indexes to exclude deleted records
DROP INDEX IF EXISTS idx_engrams_thread_id;
CREATE INDEX idx_engrams_thread_id ON engrams(thread_id) WHERE NOT is_deleted;

DROP INDEX IF EXISTS idx_engrams_relevance_score;
CREATE INDEX idx_engrams_relevance_score ON engrams(thread_id, relevance_score DESC) WHERE NOT is_deleted;

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_engrams_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS engrams_updated_at ON engrams;
CREATE TRIGGER engrams_updated_at
    BEFORE UPDATE ON engrams
    FOR EACH ROW
    EXECUTE FUNCTION update_engrams_updated_at();

COMMIT;