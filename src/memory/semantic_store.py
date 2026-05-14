from __future__ import annotations

from typing import Any, Dict, List

from src.memory.base import BaseMemoryLayer
from src.memory.local_index import MemoryRecord, get_memory


class SemanticLayer(BaseMemoryLayer):
    """Local semantic-ish retrieval using SQLite FTS5 instead of hosted vector DBs."""

    def __init__(self):
        self.memory = get_memory()

    def add(self, content: str, **kwargs) -> bool:
        record = MemoryRecord(
            source_id=kwargs.get("session_id") or kwargs.get("source_id") or "semantic",
            kind=kwargs.get("category", "preference"),
            title=kwargs.get("title", kwargs.get("category", "semantic memory")),
            content=content,
            trust=float(kwargs.get("trust", kwargs.get("trust_score", 0.65))),
            pinned=bool(kwargs.get("pinned", False)),
            valid_until=kwargs.get("valid_until"),
            metadata={k: v for k, v in kwargs.items() if k not in {"session_id", "source_id", "category", "title", "trust", "trust_score", "pinned", "valid_until"}},
        )
        self.memory.remember_sync(record)
        return True

    def search(self, query: str, limit: int = 5, **kwargs) -> List[Dict[str, Any]]:
        kinds = kwargs.get("kinds")
        return self.memory.search_sync(query, limit=limit, kinds=kinds)

    def get_essential_context(self) -> str:
        return ""


semantic_layer = SemanticLayer()


def add(content: str, **kwargs) -> bool:
    return semantic_layer.add(content, **kwargs)


def search(query: str, **kwargs) -> List[Dict[str, Any]]:
    return semantic_layer.search(query, **kwargs)
