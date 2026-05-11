import logging

logger = logging.getLogger(__name__)

import importlib.util as util

from get_root import root

TOOLS_DIR = (root.project) / "tools"

FILES_TO_IGNORE = ["base.py", "registrar.py", "registry.py", "__init__.py", "command_tool.py", "create_sandbox.py"]

def discover_tools():
    for tool_file in TOOLS_DIR.rglob("*.py"):
        if tool_file.name not in FILES_TO_IGNORE:
            yield tool_file

def register_tools():
    for tool_file in discover_tools():
        tool_name = tool_file.stem
        
        spec = util.spec_from_file_location(tool_name, tool_file)

        if spec is None or spec.loader is None:
            continue

        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        """
        # Create a unique module name based on path to avoid collisions
        # e.g., "src.tools.file_tools.read"
        module_path = f"dynamic_tool_{tool_file.stem}_{hash(str(tool_file))}"
        
        spec = util.spec_from_file_location(module_path, tool_file)
        """

        yield {
            "name": tool_name,
            "module": module,
        }

