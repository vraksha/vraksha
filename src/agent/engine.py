from dataclasses import dataclass
import logging
from pydantic_ai import Agent, RunContext

# Vraksha Core Imports
from src.memory.coordinator import MemoryCoordinator

logger = logging.getLogger(__name__)

@dataclass
class VrakshaDeps:
    """
    Dependencies are injected into the PydanticAI Engine.
    Ensures that the LLM operates within Vraksha's ethical and technical boundaries.
    """
    memory: MemoryCoordinator
    soul: str          # Personality from memory/soul.md
    rules: str         # Laws of physics from memory/rules.md
    session_id: str
    user_id: str

# The CNS (Central Nervous System)
# We define result_type=str for now, but will transition to Pydantic models 
# for structured tasks like 'consolidation'.
vraksha_agent = Agent(
    'anthropic:claude-3-5-sonnet-latest', # Default model
    deps_type=VrakshaDeps,
)

@vraksha_agent.system_prompt
async def apply_governance(ctx: RunContext[VrakshaDeps]) -> str:
    """
    The Governance Membrane: Injects Identity, Rules, and Memory.
    Ensures the agent is born into Vraksha's specific context every session.
    """
    essential_context = await ctx.deps.memory.get_essential_context_async()
    
    return f"""
    # SYSTEM RULES (IMMUTABLE)
    {ctx.deps.rules}

    # YOUR IDENTITY (SOUL)
    {ctx.deps.soul}

    # RELEVANT CONTEXT (TRI-STORE)
    {essential_context}
    """

# Implementation Note:
# Legacy tools from tools/registry.py and src/skills/ will be ported here 
# using the @vraksha_agent.tool decorator.
