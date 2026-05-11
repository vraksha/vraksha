import logging

logger = logging.getLogger(__name__)

# Necessary packages
from rich.console import Console
import textwrap

# Custom modules
from src.agent.prompts import Prompts
from src.utils.read_file import extract_content
from src.utils.changes import apply_changes
from src.utils.immutables import immutable_paths

# Skills/tools registrations
from src.skills.registry import skill_registry
from tools.registry import tool_registry

# Shared llm caller
from src.utils.call_llm import call_llm

console = Console()


MODEL_PART = "orchestrator"    # For models.yaml key
MEMORY_ROLE = "agent"           # For memory path


def _msg(role: str, content):
    return {"role": role, "content": content}


def _add(messages, role, content):
    messages.append(_msg(role, content))


def _run_tool(tool_name, tool_input, avail_tools, skills):
    """
        Tool execution dispatcher.
    """

    if any(t["name"] == tool_name for t in avail_tools):
        tool = tool_registry.get(tool_name)

        logger.info(
            f"Using '{tool.name}' on {tool_input.get('path', 'project')}"
        )

        console.log(
            f'[muted]  • {tool.name} '
            f'[accent]{tool_input.get("path", "project")}[/accent][/muted]'
        )

        res = tool.call(tool_input)
        return res.result if res else res.error

    elif any(t["name"] == tool_name for t in skills):
        skill = skill_registry.get(tool_name)

        logger.info(
            f"Delegating task to '{tool_name}' expert"
        )

        console.log(
            f'[muted]  • Delegating to '
            f'[accent]{tool_name}[/accent] skill[/muted]'
        )

        res = skill.call(tool_input)
        return res.result if res else res.error

    else:
        result = f"Error: Tool {tool_name} not found in registry."
        logger.error(result)
        return result


def _format_immutable_block() -> str:
    """Render the IMMUTABLE.yaml entries as an indented bullet list.

    The first line lands at the prompt's inherited source indent, so we
    leave it bare; continuation lines are explicitly indented to 12 spaces
    so the bullets visually align under each other.
    """
    paths = immutable_paths()

    if not paths:
        return "(none configured)"

    indent = " " * 12
    return f"- {paths[0]}" + "".join(f"\n{indent}- {p}" for p in paths[1:])


def _system():
    rules   = extract_content(filename="rules", role=MEMORY_ROLE)
    project = extract_content(filename="projects", role=MEMORY_ROLE)
    memory  = extract_content(filename="memory", role=MEMORY_ROLE)
    journal = extract_content(filename="journal", role=MEMORY_ROLE)
    soul    = extract_content(filename="soul", role=None)

    skills_available = "\n".join(
        f"- {s['name']}: {s['description']}\n{s.get('instructions', '')}"
        for s in skill_registry.as_skills()
    )

    tools_available = "\n".join(
        f"- {t['name']}: {t['description']}"
        for t in tool_registry.as_tools()
    )

    return textwrap.dedent(f"""
        ############################
        # CORE IDENTITY
        ############################
        {soul}
        
        ############################
        # PERSISTENT STATE (READ ONLY CONTEXT)
        ############################
        <journal>
        {journal}
        </journal>
        
        ############################
        # SYSTEM POLICY LAYER
        ############################
        {Prompts.system(immutable_block=_format_immutable_block())}
        
        ############################
        # EXECUTION CONTEXT
        ############################
        
        ## Tools (Preferred for any concrete action)
        {tools_available}
        
        ## Skills (Specialized reasoning modules)
        {skills_available}
        
        ############################
        # PROJECT STATE
        ############################
        <project_files>
        <file name="rules.md">{rules}</file>
        <file name="projects.yaml">{project}</file>
        <file name="memory.yaml">{memory}</file>
        </project_files>
        """
        )
# ================================================================
# Agent Loop
# ================================================================

def agent(messages: list[dict]) -> str:
    system_prompt = _system()

    skills = skill_registry.as_skills()
    avail_tools = tool_registry.as_tools()

    all_tools = [*skills, *avail_tools]

    logger.info("Prompt and tools/skills loaded!")
    logger.info("Called llm")

    response = call_llm(
        model_part=MODEL_PART,
        system=system_prompt, # Use the cached version
        tools=all_tools,
        messages=messages,
        max_tokens=1500,
        raw=True
    )

    while True:
        stop_reason = response.stop_reason
        logger.info(f"LLM stop reason: {stop_reason}")

        if stop_reason == "tool_use":
            logger.info("Stopped to use tool")
            console.log('\n[muted]  • Thinking...[/muted]')

            _add(messages, "assistant", response.content)

            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                result = _run_tool(
                    block.name,
                    block.input,
                    avail_tools,
                    skills
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result)
                })

            _add(messages, "user", tool_results)

            logger.info("Re-calling llm")

            response = call_llm(
                model_part=MODEL_PART,
                system=system_prompt,
                tools=all_tools,
                messages=messages,
                max_tokens=1500,
                raw=True
            )

            continue

        elif stop_reason == "end_turn":
            logger.info("LLM finished normally")
            break

        elif stop_reason == "max_tokens":
            logger.warning("LLM hit max tokens")

            last_block = response.content[-1]

            if last_block.type == "tool_use":

                logger.info(
                    "Confirmed that llm was mid tool use"
                    "Continuing with higher token limit"
                )

                response = call_llm(
                    model_part=MODEL_PART,
                    system=system_prompt,
                    tools=all_tools,
                    messages=messages,
                    max_tokens=3000,
                    raw=True
                )

                continue

            _add(messages, "assistant", response.content)
            _add(messages, "user", "Please continue from where you left off.")

            break

        elif stop_reason == "stop_sequence":
            logger.info("LLM hit stop sequence")

            _add(messages, "user", "Tell user about it")

            break

        elif stop_reason == "pause_turn":

            logger.info("LLM paused turn")

            _add(messages, "user", "Continue with your task if possible. If not, tell user about it")
            _add(messages, "assistant", response.content)

            break

        elif stop_reason == "refusal":
            logger.warning("LLM refused response")

            _add(messages, "user",
                "Look for alternative ways to do the task while following rules. "
                "If you can't continue, explain why and suggest alternatives."
            )

            _add(messages, "assistant", response.content)
            break

        else:
            logger.warning(f"Unknown stop reason received: {stop_reason}")

            _add(messages, "user",
                f"Unknown stop reason: {stop_reason}. Continue safely."
            )

            _add(messages, "assistant", response.content)
            break

    # ================================================================
    # FINAL OUTPUT
    # ================================================================

    text_blocks = [b.text for b in response.content if b.type == "text"]
    final_text = "".join(text_blocks)

    if not final_text:
        logger.info("Agent finished without a text response.")
        return "Agent finished without a text response."

    processed_output = apply_changes(final_text, role=MEMORY_ROLE)

    return processed_output if isinstance(processed_output, str) else final_text
