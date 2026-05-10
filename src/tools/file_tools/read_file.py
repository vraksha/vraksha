from src.tools.base import Tool

from src.utils.get_tree import get_tree
from src.tools.file_tools.resolve.resolve_within_project import resolve_path

class ReadFile(Tool):
    name = "read_file"
    action = "reading"
    description = (
            "Read a file or list a directory inside the project. "
            "If `path` is a file, returns its full UTF-8 text content. "
            "If `path` is a directory, returns a tree listing up to "
            "`max_depth` levels deep. Paths are resolved relative to "
            "the project root; absolute paths outside the project are "
            "rejected. Use this whenever you need to inspect existing "
            "code, configs, docs, or memory before deciding what to do."
        )
    input_schema = {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "File or directory path, relative to the project "
                        "root (e.g. 'src/agent/llm.py' or 'memory/')."
                    ),
                },
                "max_depth": {
                    "type": "integer",
                    "description": (
                        "Tree depth used when `path` is a directory. "
                        "Default 3."
                    ),
                    "default": 3,
                },
            },
            "required": ["path"],
        }


    def call(self, tool_input: dict) -> str:
        path_str = tool_input.get("path", "")
        max_depth = tool_input.get("max_depth", 3)
        
        result = resolve_path(path_str)
        if not result.success:
            return f"ERROR: {result.error}"

        target = result.path

        if not target.exists():
            return f"ERROR: Path '{path_str}' does not exist."

        if target.is_dir():
            try:
                tree = get_tree(target, max_depth)
                return f"DIRECTORY: {path_str}\n{tree}"
            except Exception as e:
                return f"ERROR: Could not list directory: {e}"

        try:
            content = target.read_text(encoding="utf-8")
            return f"FILE: {path_str}\n{content}"

        except UnicodeDecodeError:
            return f"ERROR: '{path_str}' is a binary file (non-UTF-8)."
            
        except Exception as e:
            return f"ERROR: Failed to read file: {e}"

def get_tool() -> Tool:
    return ReadFile()

