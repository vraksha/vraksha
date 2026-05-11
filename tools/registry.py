import logging

logger = logging.getLogger(__name__)

from tools.registrar import register_tools
from tools.base import Tool

class ToolRegistry:
    def __init__(self):
        # Using a dict for O(1) lookups
        self.tools: dict[str, Tool] = {}
        self._load()

    def _load(self):
        for entry in register_tools():
            module = entry["module"]
            if not hasattr(module, "get_tool"):
                continue

            tool = module.get_tool()
            # Strict Type Check: Ensure it's actually a Tool
            if isinstance(tool, Tool):
                self.tools[tool.name] = tool
                logger.info(f"✅ Loaded tool: {tool.name}")

    def as_tools(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema
            }
            for t in self.tools.values()
        ]

    def get(self, name: str) -> Tool | None:
        # Instant lookup
        return self.tools.get(name)

        
tool_registry = ToolRegistry()

