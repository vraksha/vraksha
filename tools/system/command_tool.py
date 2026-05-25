"""
System tool: Secure command execution.

This is a TOOL (not expert).
It delegates execution to sandbox/docker layer.
"""

from __future__ import annotations

from typing import Any, Dict

from registry.register import tool
from tools.system.sandbox.docker_sandbox import execute_in_sandbox
from tools.schemas.output import RICH_OUTPUT_SCHEMA

# =========================================================
# Tool Definition
# =========================================================

@tool(
    domain="system",
    tags=["shell", "execution", "sandbox"]
)
class RunCommandTool:
    """
    Executes shell commands inside isolated sandbox.
    """

    name = "run_command"

    description = """
    Executes shell commands inside a hardened Docker sandbox.
    No network access. Limited CPU/memory. Read-only execution environment.
    """

    input_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute"
            },
            "timeout": {
                "type": "integer",
                "description": "Execution timeout in seconds",
                "default": 30
            }
        },
        "required": ["command"]
    }

    output_schema = RICH_OUTPUT_SCHEMA

    # =====================================================
    # Execution
    # =====================================================

    def call(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        IMPORTANT:
        - MUST return structured JSON dict
        - NO string formatting for LLM
        """

        command = tool_input["command"]
        timeout = tool_input.get("timeout", 30)

        result = execute_in_sandbox(
            command=command,
            timeout=timeout
        )

        # Optional safety truncation (LLM context control)
        MAX_CHARS = 4000

        if result.get("data"):
            for k in ["stdout", "stderr"]:
                if k in result["data"] and isinstance(result["data"][k], str):
                    if len(result["data"][k]) > MAX_CHARS:
                        result["data"][k] = (
                            result["data"][k][:MAX_CHARS]
                            + "\n...[TRUNCATED]"
                        )

        return result

