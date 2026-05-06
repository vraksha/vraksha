import os

_client = None

def get_client():
    global _client
    if _client is None:
        # TODO: Initialize local Kùzu database pointing to the root memory directory
        # Example: db = kuzu.Database('memory/kuzu'); _client = kuzu.Connection(db)
        pass
    return _client

async def add_episode(content: str, session_id: str) -> None:
    # TODO: Haiku extraction logic happens BEFORE calling this, or inside here
    # TODO: Write extracted nodes/edges to Kùzu
    # TODO: Implement temporal resolution (valid_until = now for contradicted edges)
    pass

async def search(query: str) -> list:
    # TODO: Perform graph traversal or semantic/fulltext search via Kùzu
    return []
