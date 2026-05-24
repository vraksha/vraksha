from pydantic_ai import RunContext
from src.agent.bootstrap import VrakshaDeps

from registry.register import tool

#######################################################################################
# One most-essential tool for vraksha (will need to be made more robust in future tho)
# It needs search memory tool at any cost, so we keep it in boostrap file!
######################################################################################

@tool(
    enabled=True,
    domain="system",
    tags=["core", "memory"]
)
async def search_memory(
    context: RunContext[VrakshaDeps],
    query: str,
    limit: int = 8,
    kinds: list[str] | None = None
) -> dict:
    """
    Search local-indexed memory for relevant facts, preferences, and project context.
    """

    try:
        res = await context.deps.memory.search_all_async(
            query,
            limit=limit,
            kinds=kinds
        )

        return {
            "success": True,
            "data": {
                "results": res
            },
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Error searching memory: {str(e)}"
        }

        