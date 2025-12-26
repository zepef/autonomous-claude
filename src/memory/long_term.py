"""
Long-Term Memory Module (Qdrant Vector Database)
Semantic storage for learnings, strategies, and evolved patterns

Requires: pip install qdrant-client sentence-transformers
Docker: docker run -p 6333:6333 -v ./data/qdrant:/qdrant/storage qdrant/qdrant
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("[LongTerm] Warning: qdrant-client not installed. Run: pip install qdrant-client")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDER_AVAILABLE = True
except ImportError:
    EMBEDDER_AVAILABLE = False
    print("[LongTerm] Warning: sentence-transformers not installed. Run: pip install sentence-transformers")


# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "claude_memory"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions, fast
EMBEDDING_DIM = 384


class LongTermMemory:
    """
    Long-term semantic memory using Qdrant vector database.

    Stores:
    - Successful strategies and their contexts
    - Failed approaches to avoid
    - Learned patterns from classifier/honeypot
    - Evolution history with embeddings for similarity search
    """

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT):
        self.client = None
        self.embedder = None
        self._initialized = False

        if QDRANT_AVAILABLE and EMBEDDER_AVAILABLE:
            try:
                self.client = QdrantClient(host=host, port=port, timeout=10)
                self.embedder = SentenceTransformer(EMBEDDING_MODEL)
                self._ensure_collection()
                self._initialized = True
                print(f"[LongTerm] Connected to Qdrant at {host}:{port}")
            except Exception as e:
                print(f"[LongTerm] Warning: Could not connect to Qdrant: {e}")
                print("[LongTerm] Run: docker run -p 6333:6333 qdrant/qdrant")

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == COLLECTION_NAME for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM,
                        distance=Distance.COSINE
                    )
                )
                print(f"[LongTerm] Created collection: {COLLECTION_NAME}")
        except Exception as e:
            print(f"[LongTerm] Error ensuring collection: {e}")

    def is_available(self) -> bool:
        """Check if long-term memory is operational"""
        return self._initialized

    def add(
        self,
        content: str,
        mem_type: str = "fact",
        tags: List[str] = None,
        importance: int = 5,
        metadata: Dict = None
    ) -> Optional[str]:
        """
        Add a memory to long-term storage.

        Types: fact, skill, strategy, lesson, discovery, error, evolution

        Returns the point ID if successful.
        """
        if not self._initialized:
            print("[LongTerm] Not initialized - memory not stored")
            return None

        try:
            # Generate embedding
            embedding = self.embedder.encode(content).tolist()
            point_id = str(uuid.uuid4())

            # Build payload
            payload = {
                "timestamp": datetime.now().isoformat(),
                "type": mem_type,
                "tags": tags or [],
                "content": content,
                "importance": importance,
                **(metadata or {})
            }

            # Insert into Qdrant
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            return point_id

        except Exception as e:
            print(f"[LongTerm] Error adding memory: {e}")
            return None

    def search(
        self,
        query: str,
        limit: int = 5,
        mem_type: Optional[str] = None,
        min_importance: Optional[int] = None
    ) -> List[Dict]:
        """
        Semantic search for relevant memories.

        Returns list of memories sorted by relevance.
        """
        if not self._initialized:
            return []

        try:
            # Generate query embedding
            query_embedding = self.embedder.encode(query).tolist()

            # Build filter if needed
            filter_conditions = []
            if mem_type:
                filter_conditions.append(
                    FieldCondition(key="type", match=MatchValue(value=mem_type))
                )
            if min_importance:
                filter_conditions.append(
                    FieldCondition(key="importance", range={"gte": min_importance})
                )

            search_filter = Filter(must=filter_conditions) if filter_conditions else None

            # Search
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=limit,
                query_filter=search_filter
            )

            # Format results
            memories = []
            for hit in results:
                memory = hit.payload.copy()
                memory['score'] = hit.score
                memory['id'] = str(hit.id)
                memories.append(memory)

            return memories

        except Exception as e:
            print(f"[LongTerm] Search error: {e}")
            return []

    def get_by_type(self, mem_type: str, limit: int = 20) -> List[Dict]:
        """Get all memories of a specific type"""
        if not self._initialized:
            return []

        try:
            results = self.client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value=mem_type))]
                ),
                limit=limit
            )

            return [point.payload for point in results[0]]

        except Exception as e:
            print(f"[LongTerm] Error getting by type: {e}")
            return []

    def get_strategies(self, limit: int = 10) -> List[Dict]:
        """Get stored strategies sorted by importance"""
        strategies = self.get_by_type("strategy", limit=limit * 2)
        return sorted(strategies, key=lambda x: x.get("importance", 0), reverse=True)[:limit]

    def get_lessons(self, limit: int = 10) -> List[Dict]:
        """Get learned lessons"""
        return self.get_by_type("lesson", limit=limit)

    def add_successful_strategy(
        self,
        description: str,
        context: str,
        fitness_score: float,
        tags: List[str] = None
    ) -> Optional[str]:
        """Store a successful strategy for future reference"""
        content = f"Strategy: {description}\nContext: {context}\nFitness: {fitness_score}"
        return self.add(
            content=content,
            mem_type="strategy",
            tags=tags or [],
            importance=min(10, int(fitness_score * 10)),
            metadata={
                "description": description,
                "context": context,
                "fitness_score": fitness_score
            }
        )

    def add_lesson(
        self,
        lesson: str,
        source: str,
        importance: int = 5
    ) -> Optional[str]:
        """Store a learned lesson"""
        return self.add(
            content=f"{lesson} (Source: {source})",
            mem_type="lesson",
            importance=importance,
            metadata={"source": source}
        )

    def add_failure(
        self,
        description: str,
        reason: str,
        context: str
    ) -> Optional[str]:
        """Store a failure to avoid repeating"""
        return self.add(
            content=f"Failed: {description}\nReason: {reason}\nContext: {context}",
            mem_type="error",
            importance=7,  # Failures are important to remember
            metadata={
                "description": description,
                "reason": reason,
                "context": context
            }
        )

    def find_similar_strategies(self, context: str, limit: int = 3) -> List[Dict]:
        """Find strategies that worked in similar contexts"""
        return self.search(
            query=context,
            limit=limit,
            mem_type="strategy"
        )

    def get_stats(self) -> Dict:
        """Get memory statistics"""
        if not self._initialized:
            return {"status": "not_initialized"}

        try:
            collection_info = self.client.get_collection(COLLECTION_NAME)
            return {
                "status": "connected",
                "total_points": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "collection": COLLECTION_NAME
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def clear_all(self):
        """Clear all long-term memories (use with caution)"""
        if not self._initialized:
            return

        try:
            self.client.delete_collection(COLLECTION_NAME)
            self._ensure_collection()
            print("[LongTerm] All memories cleared")
        except Exception as e:
            print(f"[LongTerm] Error clearing: {e}")


# Singleton instance
_memory_instance = None


def get_long_term_memory() -> LongTermMemory:
    """Get the singleton long-term memory instance"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = LongTermMemory()
    return _memory_instance


if __name__ == "__main__":
    # Test the module
    memory = get_long_term_memory()

    if not memory.is_available():
        print("\nQdrant not available. Start with:")
        print("docker run -p 6333:6333 -v ./data/qdrant:/qdrant/storage qdrant/qdrant")
    else:
        print("\nTesting long-term memory...")

        # Add test memories
        memory.add(
            content="Classifier accuracy improved by using role-play detection",
            mem_type="lesson",
            tags=["classifier", "detection"],
            importance=8
        )

        memory.add_successful_strategy(
            description="Use BERT fine-tuned on role-play prompts",
            context="Malicious prompt classification",
            fitness_score=0.92,
            tags=["classifier", "bert"]
        )

        memory.add_failure(
            description="Simple keyword matching",
            reason="Too many false positives with security education prompts",
            context="Initial classifier approach"
        )

        # Search
        print("\nSearching for 'classifier detection':")
        results = memory.search("classifier detection", limit=3)
        for r in results:
            print(f"  [{r['type']}] {r['content'][:60]}... (score: {r['score']:.3f})")

        # Stats
        print("\nStats:")
        print(json.dumps(memory.get_stats(), indent=2))
