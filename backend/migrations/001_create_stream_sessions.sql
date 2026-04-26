-- Migration: Create stream_sessions table
-- This table tracks active playback sessions for the stream proxy
-- Created: 2024

CREATE TABLE IF NOT EXISTS stream_sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    device_id VARCHAR(255) NOT NULL,
    song_id VARCHAR(255) NOT NULL,
    audio_quality VARCHAR(20) NOT NULL DEFAULT 'high',
    bitrate INTEGER NOT NULL DEFAULT 320,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    expires_at DATETIME NOT NULL,
    last_heartbeat_at DATETIME,
    current_position_ms INTEGER DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_stream_sessions_user_id ON stream_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_stream_sessions_device_id ON stream_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_stream_sessions_song_id ON stream_sessions(song_id);
CREATE INDEX IF NOT EXISTS idx_stream_sessions_is_active ON stream_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_stream_sessions_expires_at ON stream_sessions(expires_at);

-- Index for finding expired sessions
CREATE INDEX IF NOT EXISTS idx_stream_sessions_active_ended ON stream_sessions(is_active, ended_at) 
    WHERE is_active = TRUE AND ended_at IS NULL;
