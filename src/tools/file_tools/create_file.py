from src.tools.base import Tool

from src.tools.file_tools.resolve.resolve_within_project import resolve_path

class CreateFile(Tool):
    name = "create_file"
    action = "creating"
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

    def call(self, tool_input: dict) -> str:
        path_str = tool_input.get("path", "")
        content = tool_input.get("content", "")

        result = resolve_path(path_str)
        if not result.success:
            return f"ERROR: {result.error}"

        target = result.path

        if target.exists():
            return f"ERROR: file '{path_str}' already exists. Use 'write_file' to modify it."

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"OK: created file {path_str} ({len(content)} chars)"
            
        except Exception as e:
            return f"ERROR: failed to create '{path_str}': {e}"


def get_tool() -> Tool:
    return CreateFile()
