import logging

logger = logging.getLogger(__name__)

import importlib.util as util

from tool_name import get_tool_name

from get_root import root

TOOLS_DIR = (root.project) / "tools"

FILES_TO_IGNORE = ["base.py", "registrar.py", "registry.py", "__init__.py", "command_tool.py", "create_sandbox.py"]

FOLDERS_TO_IGNORE = ["resolve"]

def discover_tools():
    for tool_file in TOOLS_DIR.rglob("*.py"):
        if (
            tool_file.name not in FILES_TO_IGNORE
            and tool_file.parent.name not in FOLDERS_TO_IGNORE
        ):
            yield tool_file

def register_tools():
    for tool_file in discover_tools():
        # tool_name = tool_file.stem
        tool_name = get_tool_name(tool_file, "tools", "farthest")

        spec = util.spec_from_file_location(tool_name, tool_file)

        if spec is None or spec.loader is None:
            continue

        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        yield {
            "name": tool_name,
            "module": module,
        }

