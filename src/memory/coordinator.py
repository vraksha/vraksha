from __future__ import annotations

import asyncio
from typing import Any, Dict, Sequence

from src.memory.local_index import LocalFirstMemory, MemoryRecord, get_memory

class MemoryCoordinator:
    """A unified gateway to orchestrate retrieval across Vraksha's Tri-Store backends.

    In a complex agentic system, the Agent (the 'Brain') should not be coupled 
    to the specific mechanics of its long-term storage. This class acts as a 
    single interface that hides the complexity of whether a fact came from 
    a Markdown file (Wiki), a conceptual store (Semantic), or the primary 
    search index (SQLite).

    By centralizing retrieval here, we can inject new storage technologies — 
    such as a Graph Database or a dedicated Vector DB — without modifying the 
    core agent engine. It ensures that the agent always interacts with a 
    consistent, high-level memory API.
    """

    def __init__(self, memory: LocalFirstMemory | None = None):
        # We default to the global singleton engine to keep things centralized.
        self.memory = memory or get_memory()

    async def get_essential_context_async(self, user_query: str = "") -> str:
        """Retrieves the bedrock identity and recent session context for the prompt."""
        return await self.memory.essential_context(user_query)

    async def search_all_async(self, query: str, *, limit: int = 8, kinds: Sequence[str] | None = None) -> Dict[str, Any]:
        """Keyword search across all indexed documents and files."""
        hits = await self.memory.search(query, limit=limit, kinds=kinds)
        return {"results": hits, "count": len(hits)}

    async def remember_many_async(self, records: list[MemoryRecord]) -> None:
        """Commits multiple facts/events to long-term storage."""
        await self.memory.remember_many(records)

    def run_background_consolidation(self, messages: list[dict[str, Any]]) -> None:
        """The 'Cognitive Sleep Cycle' for distilling chat history into durable memory.
    
        Raw conversation transcripts are extremely high-entropy environments full 
        of social filler, greetings, and ephemeral debug noise. Feeding these 
        transcripts back into the agent directly results in token bloat and a 
        significant drop in reasoning quality.
        
        Consolidation is the process of 'Garbage Collection' for the brain. It 
        uses a specialized sub-agent to analyze the transcript, extract high-signal 
        facts, rules, and preferences, and commit them to their respective 
        Tri-Store layers. This ensures that the agent's long-term memory 
        remains dense, accurate, and relevant.
        """
        from src.memory.consolidation import consolidate_session
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(consolidate_session(messages))
        except RuntimeError:
            asyncio.run(consolidate_session(messages))


memory_coordinator = MemoryCoordinator()
