# 🎯 Recommendation System Architecture

## Executive Summary

A production-ready, 4-layer recommendation system for Ethiopian Music Platform inspired by YouTube's recommendation principles. Designed to maximize user session duration and minimize skips through intelligent multi-source candidate generation, ranking, session optimization, and controlled exploration.

---

## 🏗️ Architecture Overview

### 4-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: Exploration vs Exploitation (80/20)              │
│  ├─ 80% exploitation (high-confidence recommendations)     │
│  └─ 20% exploration (diverse discovery)                    │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: Session Optimization                             │
│  ├─ No repeats within last 10 songs                        │
│  ├─ Artist diversity (no same artist twice in a row)       │
│  ├─ Genre diversity bonuses                                  │
│  └─ Skip penalty (reduce recently skipped songs)           │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: Ranking Engine                                     │
│  ├─ Completion rate: 45% weight                              │
│  ├─ Skip rate (inverse): 25% weight                        │
│  ├─ Play frequency: 20% weight                             │
│  ├─ Recency: 10% weight                                    │
│  └─ YouTube boost: up to 20% additional                    │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: Candidate Generation                               │
│  ├─ User listening history (30 songs)                      │
│  ├─ Same genre matches (40 songs)                          │
│  ├─ Same artist matches (20 songs)                         │
│  ├─ Internal trending (25 songs)                           │
│  ├─ YouTube trending (15 songs) ← 20% external signal      │
│  └─ Random exploration (10 songs)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Scoring Formula

### Base Score Calculation (80% weight)
```
base_score = (completion_rate * 45.0) +
             ((1 - skip_rate) * 25.0) +
             (play_count / 10.0 * 20.0) +
             (recency_score * 10.0)
```

### YouTube Boost (up to 20% max)
```
youtube_boost = min(
    (view_count / 100000) * 0.2,  # View-based boost
    current_score * 0.20,           # Max 20% of current score
    20.0                            # Absolute max 20 points
)

final_score = base_score + youtube_boost
```

### Hot Score (for trending)
```
hot_score = (completions * 3.0) +
            (plays * 1.0) +
            ((1 - skip_rate) * 10.0)
```

---

## 🔗 YouTube Integration (20% Signal)

### Design Principles
- **YouTube = 20% weight maximum** (weak external signal)
- **Internal system = 80% weight** (strong primary signal)
- YouTube is used for validation and trending boost only
- No user data synced with YouTube
- Region-aware (default: Ethiopia/ET)

### Implementation
```python
# YouTube provides trending music data
youtube_trending = youtube_service.get_trending_music(region_code="ET")

# Match internal songs to YouTube videos
boosts = youtube_service.match_and_boost_internal_songs(
    internal_songs,
    region="ET"
)

# Apply boost (max 20%)
for song_id, boost in boosts.items():
    final_score = base_score + min(boost.boost_score, 20.0)
```

### Caching Strategy
- YouTube trending: **Cached 2 hours**
- YouTube search results: **Cached 6 hours**
- YouTube API quotas respected

---

## 🔥 Internal Trending System

### Trending Calculation
```python
trending = calculate_trending_songs(
    location_level="global",  # or "country", "city"
    hours=24,
    limit=50
)

# Formula:
engagement_score = (completions * 2 + plays - skips) / (total + 1)
```

### Location-Based Trending
- **Global**: All users
- **Country**: Filter by country code (e.g., "ET")
- **City**: Filter by city name (e.g., "Addis Ababa")

### Cache Strategy
- Trending results: **Cached 5 minutes**
- Auto-invalidation on significant playback events

---

## 🎯 API Endpoints

### 1. GET `/recommendations/next`
Get the single best next song recommendation.

**Parameters:**
- `user_id` (required): User ID
- `current_song_id` (optional): Context for recommendations
- `location` (optional): Regional trending context

**Response:**
```json
{
  "generated_at": "2024-01-20T10:00:00Z",
  "current_song_id": "song_123",
  "recommendations": [
    {
      "song_id": "song_456",
      "title": "Ethiopian Jazz Classic",
      "artist": "Mulatu Astatke",
      "genre": "Jazz",
      "score": 87.5,
      "reasons": ["High completion rate", "Genre match: Jazz"],
      "breakdown": {
        "completion_rate": 0.85,
        "skip_rate": 0.05,
        "popularity": 15.0,
        "recency": 8.5
      },
      "source": "internal"
    }
  ]
}
```

**Cache TTL:** 5 minutes

---

### 2. GET `/recommendations/for-you`
Get personalized recommendation feed with 80/20 mix.

**Parameters:**
- `user_id` (required): User ID
- `limit` (optional): Number of recommendations (default: 12, max: 50)
- `location` (optional): Regional context

**Response:**
```json
{
  "generated_at": "2024-01-20T10:00:00Z",
  "recommendations": [
    {
      "song_id": "song_789",
      "title": "Tizita",
      "artist": "Teddy Afro",
      "score": 92.3,
      "source": "internal",
      "youtube_boost": 12.5
    }
  ]
}
```

**Cache TTL:** 30 minutes

---

### 3. GET `/recommendations/trending`
Get trending songs based on internal playback activity.

**Parameters:**
- `location` (optional): Filter by location
- `location_level` (optional): "global", "country", or "city"
- `limit` (optional): Number of songs (default: 12, max: 50)

**Response:**
```json
{
  "generated_at": "2024-01-20T10:00:00Z",
  "recommendations": [
    {
      "song_id": "song_101",
      "title": "Hot New Track",
      "artist": "New Artist",
      "play_count": 1523,
      "hot_score": 85.4,
      "metadata": {"source": "internal", "location": "global"}
    }
  ]
}
```

**Cache TTL:** 10 minutes

---

### 4. POST `/recommendations/feedback`
Record user feedback on recommendations.

**Parameters:**
- `user_id` (required): User ID
- `song_id` (required): Song that was recommended
- `action` (required): "played", "skipped", "completed", "liked", "disliked"

**Response:**
```json
{
  "status": "recorded",
  "user_id": 123,
  "song_id": "song_456",
  "action": "completed"
}
```

**Effect:** Invalidates user's recommendation cache

---

## 💾 Database Schema

### Playback Events Table
```sql
CREATE TABLE playback_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    song_id INTEGER NOT NULL REFERENCES library_songs(id),
    event_type VARCHAR(20) NOT NULL,  -- 'play', 'skip', 'complete'
    session_id INTEGER REFERENCES sessions(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_playback_user_timestamp (user_id, timestamp DESC),
    INDEX idx_playback_event_timestamp (event_type, timestamp DESC),
    INDEX idx_playback_song_timestamp (song_id, timestamp DESC),
    INDEX idx_playback_user_song (user_id, song_id, timestamp DESC),
    INDEX idx_playback_session (session_id, timestamp DESC)
);
```

### Critical Indexes
1. `idx_playback_user_timestamp` - Fast user history queries
2. `idx_playback_event_timestamp` - Trending calculations
3. `idx_playback_song_timestamp` - Song statistics
4. `idx_playback_user_song` - User's song history
5. `idx_playback_session` - Session sequences

---

## 🚀 Performance & Scalability

### Caching Strategy

| Data | Cache TTL | Backend |
|------|-----------|---------|
| User recommendations | 30 minutes | Redis |
| Next song | 5 minutes | Redis |
| Trending | 10 minutes | Redis |
| YouTube trending | 2 hours | Redis |
| Song statistics | On-demand | DB + Memory |

### Database Optimizations
- Connection pooling (20 connections default)
- Indexed queries on hot paths
- Efficient aggregation queries
- Read replicas for trending (optional)

### Async Support
- All repository methods support async
- FastAPI async endpoints
- Non-blocking YouTube API calls

---

## 📁 File Structure

```
backend/
├── app/
│   ├── api/
│   │   └── recommendations.py      # API endpoints
│   ├── services/
│   │   ├── recommendation_engine.py # 4-layer engine
│   │   └── youtube_integration.py   # YouTube service (20%)
│   ├── repositories/
│   │   └── playback_repository.py   # Data access layer
│   ├── models/
│   │   └── playback.py              # Database models
│   ├── schemas/
│   │   └── recommendation.py        # Pydantic schemas
│   ├── core/
│   │   └── cache.py                 # Redis caching
│   └── db/
│       └── recommendation_indexes.py # Index management
└── RECOMMENDATION_SYSTEM_DESIGN.md   # This document
```

---

## 🎮 Session Optimization Rules

### Diversity Controls
| Rule | Penalty/Bonus |
|------|---------------|
| Same artist as last song | -10 points |
| New artist (not in last 3) | +4 points |
| Genre change | +2.5 points |
| Genre fatigue (≥2 same) | -3 points |
| Recently skipped (24h) | -18 points |
| Already in queue | -50 points |
| Recently played (last 10) | -8 points |

### Example Flow
1. User plays "Song A" by "Artist X"
2. Next recommendation avoids "Artist X" for 1 song
3. Genre switches to maintain variety
4. Skipped songs from yesterday penalized

---

## 📈 Monitoring & Analytics

### Key Metrics
- **Recommendation CTR**: % of recommendations played
- **Skip Rate**: % of recommendations skipped
- **Session Duration**: Average listening time
- **Cache Hit Rate**: % of requests served from cache
- **YouTube Boost Impact**: Performance of YouTube-boosted songs

### Logging
```python
# Every recommendation logged
logger.info(
    f"Recommendation: user={user_id}, "
    f"song={song_id}, score={score:.2f}, "
    f"source={source}"
)

# Feedback logged
logger.info(
    f"Feedback: user={user_id}, "
    f"song={song_id}, action={action}"
)
```

---

## 🔐 Configuration

### Environment Variables
```bash
# YouTube API (20% signal)
YOUTUBE_API_KEY=your_api_key_here

# Redis Cache
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Recommendation Settings
RECOMMENDATION_CACHE_TTL=1800  # 30 minutes
TRENDING_CACHE_TTL=600         # 10 minutes
EXPLORE_RATE=0.20              # 20% exploration
```

---

## 🧪 Testing

### Test the API
```bash
# Get next recommendation
curl "http://localhost:8000/recommendations/next?user_id=1"

# Get personalized feed
curl "http://localhost:8000/recommendations/for-you?user_id=1&limit=12"

# Get trending
curl "http://localhost:8000/recommendations/trending?location=ET&limit=12"

# Record feedback
curl -X POST "http://localhost:8000/recommendations/feedback?user_id=1&song_id=song_123&action=completed"
```

---

## 🚦 Deployment Checklist

- [ ] Create database indexes
- [ ] Configure Redis cache
- [ ] Set YouTube API key (optional)
- [ ] Test all endpoints
- [ ] Verify cache invalidation
- [ ] Monitor recommendation quality
- [ ] Set up analytics logging

---

## 🎯 Success Metrics

### Goals
- **Session Duration**: +20% increase
- **Skip Rate**: < 15% for recommendations
- **Discovery Rate**: 20% of plays from exploration
- **Cache Hit Rate**: > 70%
- **API Response Time**: < 100ms (p95)

---

## 📝 Implementation Notes

### Why 80/20 Exploration?
- Prevents filter bubbles
- Enables music discovery
- Keeps recommendations fresh
- Balances safety with novelty

### Why YouTube 20%?
- Validates internal trending
- Catches external viral hits
- Provides regional context
- Doesn't dominate internal signals

### Why No ML Models?
- Faster iteration
- Explainable results
- Lower infrastructure cost
- Simpler debugging
- Still highly effective

---

## 🤝 Integration Points

### Frontend Integration
```javascript
// Get next song to play
const nextSong = await fetch(
  `/recommendations/next?user_id=${userId}&current_song_id=${currentSongId}`
);

// Get feed for "For You" page
const feed = await fetch(
  `/recommendations/for-you?user_id=${userId}&limit=12`
);

// Record feedback
await fetch(
  `/recommendations/feedback?user_id=${userId}&song_id=${songId}&action=completed`,
  { method: 'POST' }
);
```

### Playback Event Tracking
```python
# Record every playback event
playback_repo.record_event(
    user_id=user_id,
    song_id=song_id,
    event_type="complete"  # or "play", "skip"
)
```

---

## 📚 References

- YouTube Recommendation System Paper (2016)
- The Netflix Recommender System (2015)
- Spotify's Discover Weekly Algorithm
- FastAPI Best Practices
- Redis Caching Patterns

---

**Version:** 1.0  
**Last Updated:** April 2026  
**Status:** Production Ready
