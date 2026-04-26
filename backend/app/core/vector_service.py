"""
Vector service for managing vector database operations.
Provides abstraction over vector storage and search.
"""

from typing import List, Optional, Dict, Any
import logging
from app.core.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class VectorService:
    """Service for vector storage and similarity search."""
    
    def __init__(self):
        self.embedding_service = embedding_service
        self._memory_storage: Dict[str, Dict[str, Any]] = {}
    
    def add_song_vector(
        self,
        song_id: str,
        title: str,
        artist: str,
        genre: str,
        lyrics: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add a song vector to the storage.
        
        Args:
            song_id: Unique song identifier
            title: Song title
            artist: Artist name
            genre: Music genre
            lyrics: Optional lyrics
            metadata: Optional additional metadata
            
        Returns:
            True if successful
        """
        try:
            # Generate embedding
            embedding = self.embedding_service.generate_song_embedding(
                title=title,
                artist=artist,
                genre=genre,
                lyrics=lyrics
            )
            
            # Store in memory (replace with vector DB in production)
            self._memory_storage[song_id] = {
                "embedding": embedding,
                "metadata": metadata or {},
                "song_id": song_id,
                "title": title,
                "artist": artist,
                "genre": genre
            }
            
            logger.info(f"Added song vector: {song_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add song vector: {e}")
            return False
    
    def search_similar_songs(
        self,
        query_song_id: Optional[str] = None,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        genre: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar songs based on query.
        
        Args:
            query_song_id: ID of reference song
            title: Query title (for text-based search)
            artist: Query artist
            genre: Filter by genre
            top_k: Number of results
            
        Returns:
            List of similar songs with similarity scores
        """
        try:
            # Get query embedding
            if query_song_id and query_song_id in self._memory_storage:
                query_embedding = self._memory_storage[query_song_id]["embedding"]
            elif title:
                query_embedding = self.embedding_service.generate_embedding(title)
            else:
                return []
            
            # Prepare candidates
            candidates = []
            for song_id, data in self._memory_storage.items():
                # Skip the query song itself
                if song_id == query_song_id:
                    continue
                
                # Filter by genre if specified
                if genre and data.get("genre") != genre:
                    continue
                
                candidates.append((song_id, data["embedding"]))
            
            # Find similar
            similar = self.embedding_service.find_similar_embeddings(
                query_embedding,
                candidates,
                top_k=top_k
            )
            
            # Build results
            results = []
            for song_id, score in similar:
                song_data = self._memory_storage[song_id]
                results.append({
                    "song_id": song_id,
                    "title": song_data["title"],
                    "artist": song_data["artist"],
                    "genre": song_data["genre"],
                    "similarity_score": score,
                    "metadata": song_data.get("metadata", {})
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_song_vector(self, song_id: str) -> Optional[Dict[str, Any]]:
        """Get stored vector data for a song."""
        return self._memory_storage.get(song_id)
    
    def delete_song_vector(self, song_id: str) -> bool:
        """Delete a song vector from storage."""
        if song_id in self._memory_storage:
            del self._memory_storage[song_id]
            logger.info(f"Deleted song vector: {song_id}")
            return True
        return False
    
    def get_all_songs(self) -> List[Dict[str, Any]]:
        """Get all stored song vectors."""
        return list(self._memory_storage.values())

# Global vector service instance
vector_service = VectorService()
