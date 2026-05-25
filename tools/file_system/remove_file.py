import logging

logger = logging.getLogger(__name__)

from typing import Dict, Any

from resolve.resolve_within_project import resolve_path
from tools.schemas.output import STANDARD_OUTPUT_SCHEMA
from src.utils.immutables import is_immutable

from registry.register import tool

@tool(domain="filesystem", tags=["delete", "remove"])
class RemoveFile():
    name = "remove_file"
    description = (
                "Remove/delete a file inside the project. "
                "REFUSES paths outside the project root. REFUSES paths listed "
                "in memory/IMMUTABLE.yaml — those are agent-protected and "
                "must be removed by the user manually. Returns a short status "
                "string starting with OK / BLOCKED / ERROR."
            )
    input_schema = {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "File path, relative to the project root."
                        ),
                    },
                },
                "required": ["path"],
            }

    output_schema = STANDARD_OUTPUT_SCHEMA

    def call(self, tool_input: dict) -> Dict[str, Any]:
        path_str = tool_input.get("path", "")
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

        if is_immutable(target):
            error=f"BLOCKED: '{path_str}' is protected and cannot be deleted."
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
            logger.error(error)

        if not target.exists():
            error=f"ERROR: File '{path_str}' does not exist."
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
            logger.error(error)

        if target.is_dir():
            error=f"ERROR: '{path_str}' is a directory. Use a directory removal tool instead."
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
            logger.error(error)

        try:
            target.unlink()
            output=f"OK: removed {path_str}"
            return {
                "success":True,
                "data":{
                    "path": path_str,
                    "content": output
                }
            }
            logger.info(output)
            
        except Exception as e:
            error=f"ERROR: failed to delete '{path_str}': {e}"
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
            logger.error(error)

