import logging

logger = logging.getLogger(__name__)

from tools.base import Tool
from resolve.resolve_within_project import resolve_path
from resolve.resolve_result import ResolveResult
from src.utils.immutables import is_immutable

class RemoveFile(Tool):
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

    def call(self, tool_input: dict) -> str:
        path_str = tool_input.get("path", "")
        result = resolve_path(path_str)

        if not result.success:
            error=f"ERROR: {result.error}"
            return ResolveResult(
                success=False,
                error=error
            )
            logger.error(error)

        target = result.path 

        if is_immutable(target):
            error=f"BLOCKED: '{path_str}' is protected and cannot be deleted."
            return ResolveResult(
                success=False,
                error=error
            )
            logger.error(error)

        if not target.exists():
            error=f"ERROR: File '{path_str}' does not exist."
            return ResolveResult(
                success=False,
                error=error
            )
            logger.error(error)

        if target.is_dir():
            error=f"ERROR: '{path_str}' is a directory. Use a directory removal tool instead."
            return ResolveResult(
                success=False,
                error=error
            )
            logger.error(error)

        try:
            target.unlink()
            output=f"OK: removed {path_str}"
            return ResolveResult(
                success=True,
                result=output
            )
            logger.info(output)
            
        except Exception as e:
            error=f"ERROR: failed to delete '{path_str}': {e}"
            return ResolveResult(
                success=False,
                error=error
            )
            logger.error(error)


def get_tool() -> Tool:
    return RemoveFile()
    