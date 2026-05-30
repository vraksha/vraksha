from __future__ import annotations

from pydantic_ai.agent import Agent
from pydantic_ai.tools import RunContext

from src.agent.bootstrap import VrakshaDeps
from src.factory.assemble import build_system_prompt


async def build_governance_prompt(context: RunContext[VrakshaDeps]) -> str:
    essential_context = await context.deps.memory.get_essential_context_async()

    return build_system_prompt(
        soul=context.deps.soul,
        rules=context.deps.rules,
        essential_context=essential_context,
    )


def register_governance_prompt(agent: Agent) -> None:
    @agent.system_prompt
    async def apply_governance(context: RunContext[VrakshaDeps]) -> str:
        return await build_governance_prompt(context)
