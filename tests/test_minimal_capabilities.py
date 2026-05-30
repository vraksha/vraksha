from registry.discovery import discover_registry_modules
from registry.register import Registry

import pytest


def test_minimal_tool_and_expert_register_and_call():
    discover_registry_modules()

    echo_entry = Registry.get("tool.universal.echo")
    smoke_entry = Registry.get("expert.architecture.smoke_check")

    assert echo_entry is not None
    assert smoke_entry is not None

    assert echo_entry.cls().call({"text": "hello"}) == {
        "success": True,
        "data": {"text": "hello"},
        "error": None,
    }

    assert smoke_entry.cls().call({"subject": "registry"}) == {
        "success": True,
        "data": {
            "subject": "registry",
            "diagnosis": "expert path reachable",
            "instruction_files": ["experts/architecture_smoke/SKILL.md"],
        },
        "error": None,
    }


@pytest.mark.anyio
async def test_minimal_capabilities_are_agent_visible():
    from src.agent.bootstrap import bootstrap_vraksha
    from src.agent.engine import vraksha_agent
    from pydantic_ai.models.test import TestModel

    model = TestModel(call_tools=[], custom_output_text="ok")
    await vraksha_agent.run(
        "Check available capabilities.",
        deps=bootstrap_vraksha(),
        model=model,
    )

    tool_names = {
        tool.name for tool in model.last_model_request_parameters.function_tools
    }

    assert "tool_universal_echo" in tool_names
    assert "expert_architecture_smoke_check" in tool_names
