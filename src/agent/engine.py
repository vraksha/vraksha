"""Compatibility exports for the agent runtime."""

from src.agent.bridge import agent_bridge
from src.agent.runtime import create_vraksha_agent, vraksha_agent

__all__ = ["agent_bridge", "create_vraksha_agent", "vraksha_agent"]
