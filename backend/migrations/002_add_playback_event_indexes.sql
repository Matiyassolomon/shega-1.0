-- Migration: Add indexes to playback_events for performance
-- Optimizes the most common query patterns in the recommendation engine

-- Index for user activity queries (most common)
CREATE INDEX IF NOT EXISTS idx_playback_events_user_timestamp 
    ON playback_events(user_id, timestamp DESC);

-- Index for event type filtering
CREATE INDEX IF NOT EXISTS idx_playback_events_type_timestamp 
    ON playback_events(event_type, timestamp DESC);

-- Index for song statistics (trending, popular)
CREATE INDEX IF NOT EXISTS idx_playback_events_song_timestamp 
    ON playback_events(song_id, timestamp DESC);

-- Partial index for recent completions (used in trending calculations)
CREATE INDEX IF NOT EXISTS idx_playback_events_completions_7d 
    ON playback_events(user_id, song_id, timestamp DESC) 
    WHERE event_type = 'complete' AND timestamp > datetime('now', '-7 days');
