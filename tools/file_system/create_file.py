import logging

logger = logging.getLogger(__name__)

from typing import Dict, Any

from tools.schemas.output import STANDARD_OUTPUT_SCHEMA
from resolve.resolve_within_project import resolve_path

from registry.register import tool

@tool(
    domain="filesystem",
    tags=["create"]
)
class CreateFileTool:
    name = "create_file"
    description = (
                "Create a NEW file with `content`. Fails if the file already exists. "
                "Creates parent directories as needed. Use this for creating "
                "new modules, components, or documentation. REFUSES paths outside "
                "the project root."
            )
    input_schema = {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path, relative to the project root.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Initial file contents.",
                    },
                },
                "required": ["path", "content"],
            }
    output_schema = STANDARD_OUTPUT_SCHEMA

    def call(self, tool_input: dict) -> Dict[str, Any]:
        path_str = tool_input.get("path", "")
        content = tool_input.get("content", "")

        result = resolve_path(path_str)
        if not result.success:
            error=f"ERROR: {result.error}"
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
            logger.error(error)

        target = result.result

        if target.exists():
            error=f"ERROR: file '{path_str}' already exists. Use 'write_file' to modify it."
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
            logger.error(error)

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

            output=f"OK: created file {path_str} ({len(content)} chars)"

            return {
                "success":True,
                "data":{
                    "path": path_str,
                    "content": output
                }
            }
            logger.info(output)
            
        except Exception as e:
            error=f"ERROR: failed to create '{path_str}': {e}"
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": e
                }
            }
            logger.error(error)

