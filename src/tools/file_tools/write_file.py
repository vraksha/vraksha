from src.tools.base import Tool

from src.utils.immutables import is_immutable
from src.tools.file_tools.resolve.resolve_within_project import resolve_path

class WriteFile(Tool):
    name = "write_file"
    action = "writing"
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
            return f"ERROR: {result.error}"

        target = result.path

        if is_immutable(target):
            return f"BLOCKED: '{path_str}' is immutable."

        if target.exists() and target.is_dir():
            return f"ERROR: '{path_str}' is a directory, not a file."

        try:
            target.parent.mkdir(parents=True, exist_ok=True)

            file_mode = "w" if mode == "overwrite" else "a"

            with open(target, file_mode, encoding="utf-8") as f:
                f.write(content)

            action = "overwrote" if mode == "overwrite" else "appended to"
            
            return f"OK: {action} {len(content)} chars to {path_str}"

        except Exception as e:
            return f"ERROR: failed to write to '{path_str}': {e}"


def get_tool() -> Tool:
    return WriteFile()