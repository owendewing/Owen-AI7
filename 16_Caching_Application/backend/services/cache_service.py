import os
import json
import hashlib
import time
from typing import Optional, Tuple
import redis
from sentence_transformers import SentenceTransformer
import numpy as np

class CacheService:
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        
        # Initialize Redis client
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )
        
        # Initialize sentence transformer for semantic similarity
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Similarity threshold for cache hits
        self.similarity_threshold = 0.85
    
    def _get_query_hash(self, query: str) -> str:
        """Generate a hash for the query."""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get embedding for a query."""
        return self.embedding_model.encode(query)
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
    
    def _find_similar_query(self, query_embedding: np.ndarray) -> Optional[Tuple[str, float]]:
        """Find a similar query in the cache."""
        # Get all cached queries
        cached_queries = self.redis_client.hgetall("query_embeddings")
        
        best_similarity = 0.0
        best_query = None
        
        for query_hash, embedding_str in cached_queries.items():
            try:
                cached_embedding = np.array(json.loads(embedding_str))
                similarity = self._calculate_similarity(query_embedding, cached_embedding)
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_query = query_hash
            except Exception as e:
                print(f"Error processing cached query {query_hash}: {e}")
                continue
        
        if best_query:
            return best_query, best_similarity
        
        return None, 0.0
    
    async def get_cached_response(self, query: str) -> Optional[Tuple[str, str, float]]:
        """Get cached response for a query or similar query."""
        query_embedding = self._get_query_embedding(query)
        
        # First, check for exact match
        query_hash = self._get_query_hash(query)
        exact_match = self.redis_client.hget("responses", query_hash)
        
        if exact_match:
            response_data = json.loads(exact_match)
            return response_data["response"], response_data["tool_used"], 1.0
        
        # Check for similar queries
        similar_query_hash, similarity = self._find_similar_query(query_embedding)
        
        if similar_query_hash:
            cached_response = self.redis_client.hget("responses", similar_query_hash)
            if cached_response:
                response_data = json.loads(cached_response)
                return response_data["response"], response_data["tool_used"], similarity
        
        return None, None, 0.0
    
    async def cache_response(self, query: str, response: str, tool_used: str):
        """Cache a query-response pair."""
        query_hash = self._get_query_hash(query)
        query_embedding = self._get_query_embedding(query)
        
        # Store the response
        response_data = {
            "response": response,
            "tool_used": tool_used,
            "timestamp": str(int(time.time()))
        }
        
        self.redis_client.hset("responses", query_hash, json.dumps(response_data))
        
        # Store the query embedding for semantic similarity
        self.redis_client.hset("query_embeddings", query_hash, json.dumps(query_embedding.tolist()))
        
        # Set expiration (24 hours)
        self.redis_client.expire("responses", 86400)
        self.redis_client.expire("query_embeddings", 86400)
    
    async def clear_cache(self):
        """Clear all cached data."""
        self.redis_client.delete("responses")
        self.redis_client.delete("query_embeddings")
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        response_count = self.redis_client.hlen("responses")
        embedding_count = self.redis_client.hlen("query_embeddings")
        
        return {
            "cached_responses": response_count,
            "cached_embeddings": embedding_count
        } 