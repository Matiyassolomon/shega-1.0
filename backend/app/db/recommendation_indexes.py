"""
Database indexes for recommendation system performance.

These indexes are critical for high-throughput recommendation queries.
Run this after creating the playback_events table.
"""

from sqlalchemy import Index, text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def create_recommendation_indexes(db: Session):
    """
    Create all indexes needed for the recommendation system.
    Call this once after database setup.
    """
    
    # Index definitions for playback_events table
    indexes = [
        # 1. Primary query index: User history lookups
        {
            "name": "idx_playback_user_timestamp",
            "table": "playback_events",
            "columns": ["user_id", "timestamp DESC"],
            "description": "Fast user recent events queries"
        },
        
        # 2. Trending calculation index
        {
            "name": "idx_playback_event_timestamp",
            "table": "playback_events",
            "columns": ["event_type", "timestamp DESC"],
            "description": "Trending calculations by event type"
        },
        
        # 3. Song statistics index
        {
            "name": "idx_playback_song_timestamp",
            "table": "playback_events",
            "columns": ["song_id", "timestamp DESC"],
            "description": "Song-level event aggregation"
        },
        
        # 4. Composite index for user+song lookups
        {
            "name": "idx_playback_user_song",
            "table": "playback_events",
            "columns": ["user_id", "song_id", "timestamp DESC"],
            "description": "User's history with specific songs"
        },
        
        # 5. Session-based queries
        {
            "name": "idx_playback_session",
            "table": "playback_events",
            "columns": ["session_id", "timestamp DESC"],
            "description": "Session playback sequences"
        },
    ]
    
    created_count = 0
    
    for idx in indexes:
        try:
            # Check if index exists (PostgreSQL specific)
            check_sql = """
                SELECT 1 FROM pg_indexes 
                WHERE indexname = :index_name 
                AND tablename = :table_name
            """
            exists = db.execute(
                text(check_sql),
                {"index_name": idx["name"], "table_name": idx["table"]}
            ).fetchone()
            
            if exists:
                logger.info(f"Index {idx['name']} already exists")
                continue
            
            # Create index
            columns = ", ".join(idx["columns"])
            create_sql = f"""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx['name']}
                ON {idx['table']} ({columns})
            """
            
            db.execute(text(create_sql))
            db.commit()
            
            created_count += 1
            logger.info(f"Created index: {idx['name']} - {idx['description']}")
            
        except Exception as e:
            logger.warning(f"Failed to create index {idx['name']}: {e}")
            db.rollback()
    
    logger.info(f"Created {created_count} new indexes")
    return created_count


def verify_indexes(db: Session) -> dict:
    """Verify that all required indexes exist."""
    required_indexes = [
        "idx_playback_user_timestamp",
        "idx_playback_event_timestamp",
        "idx_playback_song_timestamp",
        "idx_playback_user_song",
        "idx_playback_session",
    ]
    
    result = {}
    
    for idx_name in required_indexes:
        check_sql = """
            SELECT 1 FROM pg_indexes 
            WHERE indexname = :index_name
        """
        exists = db.execute(text(check_sql), {"index_name": idx_name}).fetchone()
        result[idx_name] = bool(exists)
    
    return result


def get_index_stats(db: Session) -> list:
    """Get statistics about recommendation indexes."""
    stats_sql = """
        SELECT 
            indexname,
            tablename,
            pg_size_pretty(pg_relation_size(indexname::regclass)) as size
        FROM pg_indexes
        WHERE indexname LIKE 'idx_playback_%'
        ORDER BY pg_relation_size(indexname::regclass) DESC
    """
    
    result = db.execute(text(stats_sql))
    return [
        {
            "index": row[0],
            "table": row[1],
            "size": row[2]
        }
        for row in result
    ]
