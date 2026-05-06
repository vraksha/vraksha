import os
from qdrant_client import QdrantClient

_client = None

def get_client():
    global _client
    if _client is None:
        _client = QdrantClient(path="memory/qdrant")
    return _client

def add(content: str, user_id: str, session_id: str) -> None:
    # TODO: Generate embedding via fastembed
    # TODO: Store vector + metadata in Qdrant
    pass

def search(query: str, user_id: str, limit: int = 5) -> list:
    # TODO: Generate query embedding
    # TODO: Search Qdrant and return results
    return []
