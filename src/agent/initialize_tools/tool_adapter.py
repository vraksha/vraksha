from __future__ import annotations

from typing import Any, Dict

from pydantic_ai.agent import Agent

from registry.register import Registry


# =========================================================
# TOOL ADAPTER LAYER (MINIMAL + CLEAN)
# =========================================================

class ToolAdapter:
    """
    Converts RegistryEntry objects into PydanticAI-compatible tools.

    Design goal:
        - zero business logic
        - zero string formatting
        - purely structural bridging
    """

    def __init__(self, agent: Agent):
        self.agent = agent

    # -----------------------------------------------------
    # Core export function
    # -----------------------------------------------------

    def register_all(self) -> None:
        """
        Registers all enabled tools into the PydanticAI agent.
        """

        for key, entry in Registry.all().items():

            # Skip disabled tools
            if not entry.enabled:
                continue

            tool_cls = entry.cls

            self._register_single_tool(entry.key, tool_cls)

    # -----------------------------------------------------
    # Single tool wrapper
    # -----------------------------------------------------

    def _register_single_tool(self, tool_key: str, tool_cls: type) -> None:
        """
        Wraps a registry tool into a PydanticAI tool.
        """

        # IMPORTANT:
        # Each tool gets its own closure-safe wrapper

        @self.agent.tool_plain(name=tool_key)
        def wrapped_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
            """
            Executes a registry tool.

            Contract:
                Input: dict matching tool.input_schema
                Output: raw dict from tool.call()
            """

            tool_instance = tool_cls()

            result = tool_instance.call(tool_input)

            # Enforce strict contract:
            # tools must return dict, not string
            if not isinstance(result, dict):
                return {
                    "success": False,
                    "data": None,
                    "error": f"Tool returned invalid type: {type(result)}"
                }

            return result

        # Inject metadata for debugging / introspection
        wrapped_tool.__doc__ = tool_cls.description

