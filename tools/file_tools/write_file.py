import logging

logger = logging.getLogger(__name__)

from tools.base import Tool
from tools.resolve.resolve_within_project import resolve_path
from tools.resolve.resolve_result import ResolveResult
from src.utils.immutables import is_immutable

class WriteFile(Tool):
    name = "write_file"
    description = (
                "Write `content` to a file inside the project. Supports 'overwrite' "
                "(default) and 'append' modes. Creates the file and parent directories "
                "as needed. REFUSES paths outside the project root or listed in "
                "memory/IMMUTABLE.yaml. Returns a status string starting with "
                "OK / BLOCKED / ERROR."
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
                    "content": {
                        "type": "string",
                        "description": "Full file contents to write.",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Whether to 'overwrite' the file or 'append' to it. Default is 'overwrite'.",
                        "enum": ["overwrite", "append"],
                        "default": "overwrite",
                    },
                },
                "required": ["path", "content"],
            }

    def call(self, tool_input: dict) -> str:
        path_str = tool_input.get("path", "")
        content = tool_input.get("content", "")
        mode = tool_input.get("mode", "overwrite")

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
            error=f"BLOCKED: '{path_str}' is immutable."
            return ResolveResult(
                success=False,
                error=error
            )
            logger.error(error)
            

        if target.exists() and target.is_dir():
            error=f"ERROR: '{path_str}' is a directory, not a file."
            return ResolveResult(
                success=False,
                error=error
            )
            logger.error(error)

        try:
            target.parent.mkdir(parents=True, exist_ok=True)

            file_mode = "w" if mode == "overwrite" else "a"

            with open(target, file_mode, encoding="utf-8") as f:
                f.write(content)

            action = "overwrote" if mode == "overwrite" else "appended to"
            
            output=f"OK: {action} {len(content)} chars to {path_str}"
            return ResolveResult(
                success=True,
                result=output
            )
            logger.info(output)

        except Exception as e:
            error=f"ERROR: failed to write to '{path_str}': {e}"
            return ResolveResult(
                success=False,
                error=error
            )
            logger.error(error)


def get_tool() -> Tool:
    return WriteFile()