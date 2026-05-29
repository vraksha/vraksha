import logging
from pydantic_ai.agent import Agent
from pydantic_ai.tools import RunContext

# Vraksha Core Imports
from src.agent.bootstrap import VrakshaDeps, bootstrap_vraksha
from src.agent.initialize_tools.bootstrap_tools import attach_registry_tools
from src.factory.assemble import build_system_prompt

logger = logging.getLogger(__name__)

from pydantic_ai.models.test import TestModel

# ==============================================================================
# THE CNS (Central Nervous System) of VRAKSHA, literally!
# ==============================================================================

# Initialized with a TestModel to prevent premature API key validation.
vraksha_agent = Agent(
    TestModel(),
    deps_type=VrakshaDeps,
)

vraksha_agent = attach_registry_tools(vraksha_agent)

@vraksha_agent.system_prompt
async def apply_governance(context: RunContext[VrakshaDeps]) -> str:
    """
    Governance Membrane: delegates all prompt assembly to the factory.
    Engine stays clean — factory owns every string.
    """
    essential_context = await context.deps.memory.get_essential_context_async()

    return build_system_prompt(
        soul=context.deps.soul,
        rules=context.deps.rules,
        essential_context=essential_context,
    )

# ==============================================================================
# TOOL REGISTRATION: Ports legacy tools and skills to the new engine
# Just to prevent it from breaking while working with old tools,
# Will replace soon
# ==============================================================================


"""
##############################################################
# DEPRECATED
# But still kept just in case
##############################################################

def register_legacy_tools():
    '''
        Dynamically wraps and registers all tools from the legacy registry.
        Ensures Vraksha doesn't lose any capabilities during the current transition to pydantic ai.
    '''
    for name, tool in Registry.all():
        if name in ["search_memory", "read_file"]:
            continue # Already ported with native async logic
            
        def create_tool(t):
            @vraksha_agent.tool_plain(name=t.name)
            def legacy_tool_wrapper(tool_input: dict):
                # Preservation of Moat: Uses the original tool's logic and safety checks
                res = t.call(tool_input)

                # ResolveResult logic is kinda replaced now

                # Handle ResolveResult objects if present
                if hasattr(res, 'result'):
                    return str(res.result)

                if hasattr(res, 'error') and res.error:
                    return f"ERROR: {res.error}"

                return str(res)
            
            # Inject the original description for the LLM
            legacy_tool_wrapper.__doc__ = t.description
            return legacy_tool_wrapper

        create_tool(tool)
        logger.info(f"🔄 Bridged legacy tool: {name}")

# Initialize the dynamic toolset
register_legacy_tools()
"""



# ==============================================================================
# NATIVE CORE TOOLS (Async Optimized)
# Replaced with the dynamic registry, instead of this manual type
# ==============================================================================
'''
@vraksha_agent.tool
async def search_memory(
    context: RunContext[VrakshaDeps], 
    query: str, 
    limit: int = 8, 
    kinds: list[str] | None = None
) -> str:
    """
        Search local-indexed memory for relevant facts, preferences, and project context.
    """
    try:
        res = await context.deps.memory.search_all_async(query, limit=limit, kinds=kinds)
        import json
        return json.dumps(res, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"Error searching memory: {e}"
'''

"""
##########################################################
# DEPRECATED
# There is already a read_file tool out there
##########################################################
@vraksha_agent.tool
async def read_file(
    ctx: RunContext[VrakshaDeps], 
    path: str, 
    max_depth: int = 3
) -> str:
    '''
        Read a file or list a directory inside the project.
    '''
    res = resolve_path(path)
    if not res.success:
        return f"ERROR: {res.error}"

    target = res.result
    if not target.exists():
        return f"ERROR: Path '{path}' does not exist."

    if target.is_dir():
        try:
            tree = get_tree(target, max_depth)
            return f"DIRECTORY: {path}\n{tree}"
        except Exception as e:
            return f"ERROR: Could not list directory: {e}"

    try:
        content = target.read_text(encoding="utf-8")
        return f"FILE: {path}\n{content}"

    except UnicodeDecodeError:
        return f"ERROR: '{path}' is a binary file (non-UTF-8)."

    except Exception as e:
        return f"ERROR: Failed to read file: {e}"
"""

# ==============================================================================
# LEGACY BRIDGE: Ensures 100% backward compatibility with the old loop.
# ==============================================================================

from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart
from src.providers.client import get_model_priorities

def agent_bridge(messages: list[dict]) -> dict:
    """
    Synchronous bridge for the old base_loop.py.
    Now with Multi-Provider Fallback!
    """
    # 1. Bootstrap Vraksha
    deps = bootstrap_vraksha()
    
    # 2. Translate Message History
    pydantic_history = []
    last_query = "Hello"

    for msg in messages:
        role, content = msg.get("role"), msg.get("content", "")

        if role == "user":
            pydantic_history.append(ModelRequest(parts=[UserPromptPart(content=content)]))
            last_query = content

        elif role == "assistant":
            pydantic_history.append(ModelResponse(parts=[TextPart(content=content)]))

    if pydantic_history and isinstance(pydantic_history[-1], ModelRequest):
        pydantic_history.pop()

    # 3. Get Prioritized Models for 'orchestrator' task
    model_chain = get_model_priorities("orchestrator")

    if not model_chain:
        return "ERROR: No valid API keys found. Please check your .env file."

    # 4. Resilient Execution Loop
    last_error = None
    provider_errors = []

    attempted_models = []

    for model_candidate in model_chain:
        model_inst = None
        try:
            model_inst = model_candidate.instantiate()
            if not model_inst:
                raise RuntimeError(f"Provider {model_candidate} could not be initialized.")

            attempted_models.append(model_inst)
            logger.info(f"🚀 Attempting run with: {model_inst}")
            result = vraksha_agent.run_sync(
                last_query, 
                deps=deps,
                model=model_inst,
                message_history=pydantic_history if pydantic_history else None
            )
            return result.output

        except Exception as e:
            from src.error_handlers.extract import extract_error_info
            failed_model = model_inst or model_candidate
            last_error = extract_error_info(e, failed_model)
            provider_errors.append((str(failed_model), last_error))
            logger.warning(
                "⚠️ Provider %s failed | status=%s | model=%s | error=%s%s",
                failed_model,
                last_error["status_code"],
                last_error["model_name"],
                last_error["message"],
                f" | help={last_error['help_url']}" if last_error["help_url"] else ""
            )
            continue

    # 5. Agentic Failure Report (The Last Stand)
    # If we reached here, every configured provider failed.
    primary_failure = provider_errors[0][1] if provider_errors else last_error
    primary_provider = provider_errors[0][0] if provider_errors else "unknown"
    retry_line = (
        f"        › Retry    : Provider suggested retrying after {primary_failure['retry_after']}"
        if primary_failure.get("retry_after")
        else ""
    )
    help_line = f"        › Help     : {primary_failure['help_url']}" if primary_failure.get("help_url") else ""
    detail_lines = primary_failure.get("details") or []
    primary_details = "\n".join(
        f"            {line}"
        for line in detail_lines[:4]
    )
    primary_details_block = f"        › Details  :\n{primary_details}" if primary_details else ""
    failure_lines = "\n".join(
        (
            f"        › {provider}: "
            f"{error['category']} | status={error['status_code']} | "
            f"model={error['model_name']} | {error['message']}"
        )
        for provider, error in provider_errors
    )

    error_summary = f"""
        ▲ Vraksha: COGNITIVE BLOCKAGE DETECTED
        ────────────────────────────────────────────────────────────
        I could not complete the request because every configured provider failed.

        PRIMARY FAILURE:
        › Provider : {primary_provider}
        › Status   : {primary_failure["status_code"]}
        › Model    : {primary_failure["model_name"]}
        › Cause    : {primary_failure["likely_cause"]}
        › Error    : {primary_failure["message"]}
{primary_details_block}
{retry_line}
{help_line}

        WHAT TO DO:
        › {primary_failure["suggested_fix"]}

        PROVIDER ATTEMPTS:
{failure_lines}

        FALLBACK STATUS:
        › Attempted Providers: {', '.join(str(m) for m in attempted_models) or ', '.join(str(m) for m in model_chain)}
        ────────────────────────────────────────────────────────────
    """
    return error_summary
