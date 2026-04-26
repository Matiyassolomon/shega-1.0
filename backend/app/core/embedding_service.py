"""
Embedding service for vector search and similarity matching.
"""

import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing embeddings."""
    
    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self.dimension = 128  # Default embedding dimension
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector from text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        # Placeholder implementation - replace with actual model
        # In production, use sentence-transformers or OpenAI embeddings
        np.random.seed(hash(text) % 2**32)
        embedding = np.random.randn(self.dimension).tolist()
        return embedding
    
    def generate_song_embedding(
        self, 
        title: str, 
        artist: str, 
        genre: str,
        lyrics: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for a song based on its metadata.
        
        Args:
            title: Song title
            artist: Artist name
            genre: Music genre
            lyrics: Optional lyrics text
            
        Returns:
            Embedding vector
        """
        # Combine song metadata into a single text
        text = f"{title} by {artist}. Genre: {genre}."
        if lyrics:
            text += f" Lyrics: {lyrics[:500]}"  # Limit lyrics length
        
        return self.generate_embedding(text)
    
    def calculate_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def find_similar_embeddings(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[tuple],
        top_k: int = 10
    ) -> List[tuple]:
        """
        Find most similar embeddings from candidates.
        
        Args:
            query_embedding: Query vector
            candidate_embeddings: List of (id, embedding) tuples
            top_k: Number of results to return
            
        Returns:
            List of (id, similarity_score) tuples sorted by similarity
        """
        similarities = []
        
        for item_id, embedding in candidate_embeddings:
            similarity = self.calculate_similarity(query_embedding, embedding)
            similarities.append((item_id, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]

# Global embedding service instance
embedding_service = EmbeddingService()
