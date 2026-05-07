"""First-class file tools for the agent.

Two tools, modelled after `command_tool`:

- read_file(path, max_depth=3)
    File path  → returns full text content.
    Directory  → returns a tree listing (via `get_tree`).

- write_file(path, content, mode='overwrite')
    Writes `content` to a file. Supports 'overwrite' and 'append'.
    Creates parent dirs as needed.
    Refuses paths that resolve outside the project root.
    Refuses paths listed in memory/IMMUTABLE.yaml.

Both tools resolve all paths relative to the project root so the agent
cannot escape it.
"""

from pathlib import Path
import logging

from get_root import root
from src.utils.immutables import is_immutable
from src.utils.get_tree import get_tree

logger = logging.getLogger(__name__)

PROJECT_ROOT = root.project


def _resolve_within_project(path: str) -> Path:
    """Resolve `path` and ensure it lives under PROJECT_ROOT.

    Accepts both relative (preferred) and absolute paths.
    Raises ValueError if the resolved path escapes the project root,
    protects against `../`-style traversal and absolute-path escapes alike.
    """

    p = Path(path)

    if not p.is_absolute():
        p = PROJECT_ROOT / p

    p = p.resolve()
    project_resolved = PROJECT_ROOT.resolve()

    try:
        p.relative_to(project_resolved)

    except ValueError:
        raise ValueError(
            f"path '{path}' resolves outside the project root "
            f"({project_resolved}); refusing to access"
        )
    return p


class FileTools:
    def __init__(self):
        self.read_file_tool = {
            "name": "read_file",
            "description": (
                "Read a file or list a directory inside the project. "
                "If `path` is a file, returns its full UTF-8 text content. "
                "If `path` is a directory, returns a tree listing up to "
                "`max_depth` levels deep. Paths are resolved relative to "
                "the project root; absolute paths outside the project are "
                "rejected. Use this whenever you need to inspect existing "
                "code, configs, docs, or memory before deciding what to do."
            ),
            "input_schema": {
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
            },
        }

        self.write_file_tool = {
            "name": "write_file",
            "description": (
                "Write `content` to a file inside the project. Supports 'overwrite' "
                "(default) and 'append' modes. Creates the file and parent directories "
                "as needed. REFUSES paths outside the project root or listed in "
                "memory/IMMUTABLE.yaml. Returns a status string starting with "
                "OK / BLOCKED / ERROR."
            ),
            "input_schema": {
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
            },
        }

        self.create_file_tool = {
            "name": "create_file",
            "description": (
                "Create a NEW file with `content`. Fails if the file already exists. "
                "Creates parent directories as needed. Use this for creating "
                "new modules, components, or documentation. REFUSES paths outside "
                "the project root."
            ),
            "input_schema": {
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
            },
        }

        self.remove_file_tool = {
            "name": "remove_file",
            "description": (
                "Remove/delete a file inside the project. "
                "REFUSES paths outside the project root. REFUSES paths listed "
                "in memory/IMMUTABLE.yaml — those are agent-protected and "
                "must be removed by the user manually. Returns a short status "
                "string starting with OK / BLOCKED / ERROR."
            ),
            "input_schema": {
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
            },
        }

    # dispatch
    def handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "read_file":
            return self._read(
                tool_input["path"],
                tool_input.get("max_depth", 3),
            )

        if tool_name == "write_file":
            return self._write(
                tool_input["path"],
                tool_input["content"],
                tool_input.get("mode", "overwrite")
            )

        if tool_name == "create_file":
            return self._create(tool_input["path"], tool_input["content"])

        if tool_name == "remove_file":
            return self._remove(tool_input["path"])

        raise ValueError(f"FileTools: unknown tool '{tool_name}'")

    # read
    def _read(self, path: str, max_depth: int) -> str:
        try:
            target = _resolve_within_project(path)

        except ValueError as e:
            return f"ERROR: {e}"

        if not target.exists():
            return f"ERROR: path '{path}' does not exist"

        if target.is_dir():
            return f"DIRECTORY: {path}\n{get_tree(target, max_depth)}"

        try:
            content = target.read_text(encoding="utf-8")

        except UnicodeDecodeError:
            return f"ERROR: '{path}' is not a UTF-8 text file"

        except Exception as e:
            return f"ERROR: failed to read '{path}': {e}"

        return f"FILE: {path}\n{content}"

    # write
    def _write(self, path: str, content: str, mode: str = "overwrite") -> str:
        try:
            target = _resolve_within_project(path)

        except ValueError as e:
            return f"ERROR: {e}"

        if is_immutable(target):
            return (
                f"BLOCKED: '{path}' is protected by memory/IMMUTABLE.yaml "
                f"and cannot be modified by the agent. Tell the user to "
                f"edit it manually."
            )

        if target.exists() and target.is_dir():
            return f"ERROR: '{path}' is a directory, not a file"

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Use "w" for overwrite, "a" for append. Both create if missing.
            file_mode = "w" if mode == "overwrite" else "a"
            
            with open(target, file_mode, encoding="utf-8") as f:
                f.write(content)
            
        except Exception as e:
            return f"ERROR: failed to write '{path}': {e}"

        action = "overwrote" if mode == "overwrite" else "appended to"
        return f"OK: {action} {len(content)} chars to {path}"

    # create
    def _create(self, path: str, content: str) -> str:
        try:
            target = _resolve_within_project(path)

        except ValueError as e:
            return f"ERROR: {e}"

        if target.exists():
            return f"ERROR: file '{path}' already exists. Use 'write_file' to modify it."

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        except Exception as e:
            return f"ERROR: failed to create '{path}': {e}"

        return f"OK: created file {path} ({len(content)} chars)"

    # remove/delete
    def _remove(self, path:str) -> str:
        try:
            target = _resolve_within_project(path)

        except ValueError as e:
            return f"ERROR: {e}"

        if is_immutable(target):
            return (
                f"BLOCKED: '{path}' is protected by memory/IMMUTABLE.yaml "
                f"and cannot be modified by the agent. Tell the user to "
                f"edit it manually."
            )

        if target.exists() and target.is_dir():
            return f"ERROR: '{path}' is a directory, not a file"

        try:
            target.unlink(missing_ok=True)
        
        except Exception as e:
            return f"ERROR: failed to delete '{path}': {e}"

        return f"OK: removed {path}"

file_tools = FileTools()
