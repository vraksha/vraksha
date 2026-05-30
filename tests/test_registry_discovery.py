from registry.discovery import discover_registry_modules
from registry.register import Registry


def test_discovery_registers_enabled_decorators_and_skips_disabled(tmp_path, monkeypatch):
    package = tmp_path / "plugin_pack"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "enabled_tool.py").write_text(
        """
from registry.register import tool

@tool(enabled=True, domain="demo", tags=["ok"])
class EnabledTool:
    name = "enabled_tool"
    description = "Enabled test tool."
    input_schema = {"type": "object", "properties": {}, "required": []}
    output_schema = {"type": "object", "properties": {}}

    def call(self, tool_input):
        return {"success": True}
""",
        encoding="utf-8",
    )
    (package / "disabled_tool.py").write_text(
        """
from registry.register import tool

@tool(enabled=False, domain="demo", tags=["off"])
class DisabledTool:
    name = "disabled_tool"
    description = "Disabled test tool."
    input_schema = {"type": "object", "properties": {}, "required": []}
    output_schema = {"type": "object", "properties": {}}

    def call(self, tool_input):
        return {"success": True}
""",
        encoding="utf-8",
    )

    previous_registry = Registry._registry.copy()
    Registry._registry.clear()
    monkeypatch.syspath_prepend(str(tmp_path))

    try:
        errors = discover_registry_modules(tmp_path)

        assert errors == []
        assert "tool.demo.enabled_tool" in Registry.all()
        assert "tool.demo.disabled_tool" not in Registry.all()
    finally:
        Registry._registry.clear()
        Registry._registry.update(previous_registry)
