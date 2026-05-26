import logging

logger = logging.getLogger(__name__)

from typing import Dict, Any

from resolve.resolve_within_project import resolve_path
from tools.schemas.output import STANDARD_OUTPUT_SCHEMA
from src.utils.get_tree import get_tree

from registry.register import tool

@tool(domain="filesystem", tags=["read"])
class ReadFile():
    name = "read_file"
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

    output_schema = STANDARD_OUTPUT_SCHEMA


    def call(self, tool_input: dict) -> Dict[str, Any]:
        path_str = tool_input.get("path", "")
        max_depth = tool_input.get("max_depth", 3)
        
        res = resolve_path(path_str)
        if not res.success:
            error=f"ERROR: {res.error}"
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
            logger.error(error)

        target = res.result

        if not target.exists():
            error=f"ERROR: Path '{path_str}' does not exist."
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
            logger.error(error)

        if target.is_dir():
            try:
                tree = get_tree(target, max_depth)
                output=f"DIRECTORY: {path_str}\n{tree}"
                return {
                "success":True,
                "data":{
                    "path": path_str,
                    "content": output
                }
            }
                logger.info(output)

            except Exception as e:
                error=f"ERROR: Could not list directory: {e}"
                return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
                logger.error(error)

        try:
            content = target.read_text(encoding="utf-8")
            output=f"FILE: {path_str}\n{content}"
            return {
                "success":True,
                "data":{
                    "path": path_str,
                    "content": content
                }
            }
            logger.info(output)

        except UnicodeDecodeError:
            error=f"ERROR: '{path_str}' is a binary file (non-UTF-8)."
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
            logger.error(error)
            
        except Exception as e:
            error=f"ERROR: Failed to read file: {e}"
            return {
                "success":False,
                "error":{
                    "path": path_str,
                    "content": error
                }
            }
