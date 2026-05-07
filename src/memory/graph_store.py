import os
import kuzu

_client = None

def get_client():
    global _client
    if _client is None:
        db = kuzu.Database("memory/kuzu")
        _client = kuzu.Connection(db)
    return _client

async def add_episode(content: str, session_id: str) -> None:
    # TODO: Extraction logic happens BEFORE calling this, or inside here
    # TODO: Write extracted nodes/edges to Kùzu
    # TODO: Implement temporal resolution (valid_until = now for contradicted edges)
    pass

async def search(query: str) -> list:
    # TODO: Perform graph traversal or semantic/fulltext search via Kùzu
    return []
