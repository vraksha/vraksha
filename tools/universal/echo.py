from __future__ import annotations

from typing import Any, Dict

from registry.register import tool
from tools.schemas.output import STANDARD_OUTPUT_SCHEMA


@tool(enabled=True, domain="universal", tags=["smoke", "deterministic"])
class EchoTool:
    name = "echo"
    description = "Return the provided text unchanged for capability plumbing checks."
    input_schema = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to return unchanged.",
            }
        },
        "required": ["text"],
    }
    output_schema = STANDARD_OUTPUT_SCHEMA

    def call(self, tool_input: dict) -> Dict[str, Any]:
        text = str(tool_input.get("text", ""))

        return {
            "success": True,
            "data": {"text": text},
            "error": None,
        }
