from __future__ import annotations

import json

from experts.base import Skill
from src.memory.coordinator import memory_coordinator
from resolve.resolve_result import ResolveResult


class SearchMemorySkill(Skill):
    name = "search_memory"
    description = "Search local-first indexed memory for relevant facts, preferences, rules, and project context."
    instructions = "Provide a concise query. Optional: limit and kinds. Results are local SQLite FTS records gated by trust and validity."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search term or question to query memory."},
            "limit": {"type": "integer", "description": "Maximum number of results to return.", "default": 8},
            "kinds": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional memory kinds to search, e.g. preference, fact, rule, project, episode.",
            },
        },
        "required": ["query"],
    }

    def call(self, tool_input: dict) -> ResolveResult:
        query = str(tool_input.get("query", "")).strip()
        if not query:
            return ResolveResult(success=False, error="Query parameter is required for search_memory.")

        try:
            results = memory_coordinator.search_all(
                query,
                limit=int(tool_input.get("limit", 8)),
                kinds=tool_input.get("kinds"),
            )
            return ResolveResult(success=True, result=json.dumps({
                "status": "success",
                "query": query,
                "data": results,
            }, indent=2, ensure_ascii=False))
        except Exception as e:
            return ResolveResult(success=False, error=json.dumps({
                "status": "error",
                "query": query,
                "reason": str(e),
            }, ensure_ascii=False))


def get_skill() -> Skill:
    return SearchMemorySkill()
