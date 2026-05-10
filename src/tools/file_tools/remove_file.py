from src.tools.base import Tool

from src.utils.immutables import is_immutable
from src.tools.file_tools.resolve.resolve_within_project import resolve_path

class RemoveFile(Tool):
    name = "remove_file"
    action = "removing"
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
            return f"ERROR: {result.error}"

        target = result.path 

        if is_immutable(target):
            return f"BLOCKED: '{path_str}' is protected and cannot be deleted."

        if not target.exists():
            return f"ERROR: File '{path_str}' does not exist."

        if target.is_dir():
            return f"ERROR: '{path_str}' is a directory. Use a directory removal tool instead."

        try:
            target.unlink()
            return f"OK: removed {path_str}"
            
        except Exception as e:
            return f"ERROR: failed to delete '{path_str}': {e}"


def get_tool() -> Tool:
    return RemoveFile()
    