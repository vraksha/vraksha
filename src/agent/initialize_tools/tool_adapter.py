from __future__ import annotations

import inspect
from typing import Annotated, Any, Dict

from pydantic import Field
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
        # Pydantic AI / LLM APIs require tool names to match ^[a-zA-Z0-9_-]+$
        safe_name = tool_key.replace(".", "_")

        schema = getattr(tool_cls, "input_schema", {})
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        parameters = []
        for prop_name, prop_info in properties.items():
            t_str = prop_info.get("type", "any")
            if t_str == "string":
                p_type = str
            elif t_str == "integer":
                p_type = int
            elif t_str == "number":
                p_type = float
            elif t_str == "boolean":
                p_type = bool
            elif t_str == "array":
                p_type = list
            elif t_str == "object":
                p_type = dict
            else:
                p_type = Any
            
            description = prop_info.get("description", "")
            if description:
                annotated_type = Annotated[p_type, Field(description=description)]
            else:
                annotated_type = p_type

            if prop_name in required:
                default_val = inspect.Parameter.empty
            else:
                default_val = prop_info.get("default", None)

            param = inspect.Parameter(
                name=prop_name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default_val,
                annotation=annotated_type
            )
            parameters.append(param)

        sig = inspect.Signature(parameters=parameters, return_annotation=Dict[str, Any])

        def wrapped_tool(**kwargs) -> Dict[str, Any]:
            tool_instance = tool_cls()
            result = tool_instance.call(kwargs)

            # Enforce strict contract: tools must return dict
            if not isinstance(result, dict):
                return {
                    "success": False,
                    "data": None,
                    "error": f"Tool returned invalid type: {type(result)}"
                }

            return result

        # Apply signature and metadata to the wrapper function
        wrapped_tool.__signature__ = sig
        wrapped_tool.__doc__ = getattr(tool_cls, "description", "")
        wrapped_tool.__name__ = safe_name

        # Register it with the agent
        self.agent.tool_plain(name=safe_name)(wrapped_tool)

