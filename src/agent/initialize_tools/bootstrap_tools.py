from pydantic_ai.agent import Agent

from src.agent.initialize_tools.tool_adapter import ToolAdapter


def attach_registry_tools(agent: Agent) -> Agent:
    """
    One-line bootstrap function.

    This is your ONLY integration point.
    """

    adapter = ToolAdapter(agent)
    adapter.register_all()

    return agent