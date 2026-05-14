"""
Wiki Memory Layer for Vraksha.

The Wiki layer acts as the 'Immutable Truth' for the agent. It stores high-level
policies, project-wide rules, and core identity traits that should persist 
across all sessions and be prioritized during retrieval.

Unlike the Semantic or Graph stores, the Wiki is backed by curated Markdown 
files in the `memory/wiki/` directory.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from get_root import root
from src.memory.base import BaseMemoryLayer
from src.memory.local_index import MemoryRecord, bounded_read_text, get_memory, atomic_append

ROOT = root.project
MEMORY_ROOT = ROOT / "memory"
WIKI_PATH = MEMORY_ROOT / "wiki"


class WikiLayer(BaseMemoryLayer):
    """
    Manages the 'Wiki' portion of the Tri-Store. 
    Focuses on durable, manually or semi-automatically curated truths.
    """

    def __init__(self):
        WIKI_PATH.mkdir(parents=True, exist_ok=True)
        self.memory = get_memory()

    def add(self, content: str, filename: str = "rules.md", **kwargs) -> bool:
        """
        Appends new content to a wiki file and indexes it in the memory layer.
        
        Args:
            content: The text to add.
            filename: The target wiki file (e.g., 'rules.md', 'identity.md').
            **kwargs: Metadata (trust, pinned, etc.)
        """
        # Sanitize filename to prevent path traversal
        clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)
        if not clean_name.endswith(".md"):
            clean_name += ".md"
            
        path = WIKI_PATH / clean_name
        
        # Ensure thread-safe and durable filesystem write
        atomic_append(path, f"\n\n{content.strip()}\n")
        
        # Update the search index immediately
        self.memory.remember_many_sync([MemoryRecord(
            source_id=f"wiki/{path.name}",
            kind="wiki",
            title=path.name,
            content=content,
            trust=float(kwargs.get("trust", 0.90)),
            pinned=bool(kwargs.get("pinned", True)), # Wiki is usually pinned
            metadata={"filename": path.name, "curated": True},
        )])
        return True

    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Keyword search across all wiki entries."""
        return self.memory.search_sync(
            query, 
            limit=int(kwargs.get("limit", 5)), 
            kinds=["wiki", "core"]
        )

    def get_essential_context(self) -> str:
        """
        Retrieves the 'Soul' and 'Rules' that form the bedrock of the 
        agent's personality and constraints.
        """
        parts: list[str] = []
        # Priority-ordered core files
        for label, path in [
            ("soul.md", MEMORY_ROOT / "soul.md"),
            ("rules.md", MEMORY_ROOT / "rules.md"),
            ("wiki/rules.md", WIKI_PATH / "rules.md"),
        ]:
            if path.exists():
                parts.append(f"### {label}\n{bounded_read_text(path)}")
        
        return "\n\n".join(parts)


wiki_layer = WikiLayer()


def load_wiki() -> str:
    """Helper for legacy components to load the essential context."""
    return wiki_layer.get_essential_context()
