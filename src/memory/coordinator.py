from __future__ import annotations

import asyncio
from abc import ABC
from typing import Any, Dict, Sequence

from src.memory.local_index import LocalFirstMemory, MemoryRecord, get_memory


class MemoryCoordinator:
    """
    The central orchestrator for Vraksha's Tri-Store memory architecture.
    
    It manages the flow of information between the main agent loop and the 
    specialized storage layers (SQLite FTS, Local Filesystem, etc.). It 
    ensures that retrieval is fast, relevant, and contextually aware.
    """

    def __init__(self, memory: LocalFirstMemory | None = None):
        # Default to the shared LocalFirstMemory singleton
        self.memory = memory or get_memory()

    async def get_essential_context_async(self, user_query: str = "") -> str:
        return await self.memory.essential_context(user_query)

    def get_essential_context(self, user_query: str = "") -> str:
        return self.memory.essential_context_sync(user_query)

    async def search_all_async(self, query: str, *, limit: int = 8, kinds: Sequence[str] | None = None) -> Dict[str, Any]:
        hits = await self.memory.search(query, limit=limit, kinds=kinds)
        return {"results": hits, "count": len(hits)}

    def search_all(self, query: str, *, limit: int = 8, kinds: Sequence[str] | None = None) -> Dict[str, Any]:
        hits = self.memory.search_sync(query, limit=limit, kinds=kinds)
        return {"results": hits, "count": len(hits)}

    async def remember_async(self, record: MemoryRecord) -> None:
        await self.memory.remember_many([record])

    def remember(self, record: MemoryRecord) -> None:
        self.memory.remember_many_sync([record])

    async def remember_many_async(self, records: list[MemoryRecord]) -> None:
        await self.memory.remember_many(records)

    def remember_many(self, records: list[MemoryRecord]) -> None:
        self.memory.remember_many_sync(records)

    def run_background_consolidation(self, messages: list[dict[str, Any]]) -> None:
        from src.memory.consolidation import consolidate_session

        try:
            loop = asyncio.get_running_loop()

        except RuntimeError:
            asyncio.run(consolidate_session(messages))
            
        else:
            loop.create_task(consolidate_session(messages))


memory_coordinator = MemoryCoordinator()
