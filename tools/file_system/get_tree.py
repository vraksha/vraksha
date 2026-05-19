import logging

logger = logging.getLogger(__name__)

from pathlib import Path

from tools.schemas.output import STANDARD_OUTPUT_SCHEMA

from registry.register import tool

# Directories we never descend into: noisy and rarely useful to the agent.
_PRUNE = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".pytest_cache", ".mypy_cache", "dist", "build", ".next",
}

@tool(domain="filesystem", tags=["tree", "inspect"])
class GetTree():
    name="get_tree_structure"
    description=(
        "Return a textual tree of `root_path` up to `max_depth` levels deep."
        "Directory tree rendering for the read_file tool."

        "When `read_file` is given a directory, it returns this tree representation"
        "instead of file content."

        "Output mirrors `tree(1)`:"
        """
            root_dir/
            ├── file_a.py
            ├── sub/
            │   ├── file_b.py
            │   └── file_c.py
            └── file_d.md
        """
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

    output_schema = STANDARD_OUTPUT_SCHEMA


    def call(self, tool_input) -> str:
        """Return a textual tree of `root_path` up to `max_depth` levels deep.

        Output mirrors `tree(1)`:

            root_dir/
            ├── file_a.py
            ├── sub/
            │   ├── file_b.py
            │   └── file_c.py
            └── file_d.md
        """
        root_path = Path(tool_input.get("path"))

        if not root_path.exists():
            error=f"(path not found: {root_path})"
            return {
                "success":False,
                "error":{
                    "path": root_path,
                    "content": error
                }
            }
            logger.error(error)

        if root_path.is_file():
            result=root_path.name
            return {
                "success":True,
                "error":{
                    "path": root_path,
                    "content": result
                }
            }
            logger.info(f"File detected - returned '{result}'")

        lines = [f"{root_path.name}/"]
        self._walk(root_path, "", lines, tool_input.get("max_depth", 3), depth=0)
        result="\n".join(lines)
        return {
                "success":True,
                "error":{
                    "path": root_path,
                    "content": result
                }
            }
        logger.info(f"Directory detected - returned '{result}'")


    def _walk(self, path: Path, prefix: str, out: list[str], max_depth: int, depth: int):
        if depth >= max_depth:
            return

        try:
            entries = sorted(
                [
                    p for p in path.iterdir()
                    if p.name not in _PRUNE and not p.name.startswith(".")
                ],
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except PermissionError:
            return

        for i, entry in enumerate(entries):
            last = i == len(entries) - 1

            connector = "└── " if last else "├── "
            suffix = "/" if entry.is_dir() else ""

            out.append(f"{prefix}{connector}{entry.name}{suffix}")

            if entry.is_dir():
                extension = "    " if last else "│   "
                self._walk(entry, prefix + extension, out, max_depth, depth + 1)

