# Necessary packages
from rich.console import Console

# Custom modules
from src.agent.prompts import Prompts
from src.utils.read_file import extract_content
from src.utils.changes import apply_changes

from src.utils.command_tool import command_tool
from src.utils.file_tools import file_tools
from src.utils.immutables import immutable_paths

# Skills registrations
from src.skills.registry import registry

# Shared llm caller
from src.utils.call_llm import call_llm

console = Console()


MODEL_PART = "orchestrator"    # For models.yaml key
MEMORY_ROLE = "agent"           # For memory path


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
    # Memory files inlined for the agent's working context
    rules   = extract_content(filename="rules",    role=MEMORY_ROLE)
    project = extract_content(filename="projects", role=MEMORY_ROLE)
    memory  = extract_content(filename="memory",   role=MEMORY_ROLE)

    skills_available = "\n".join(
        f"- {skill.name}: {skill.description}\n{skill.instructions}"
        for skill in registry.skills
    )

    _SYSTEM_PROMPT = f"""
            - If the user wants to exit or leave or end the conversation, say something to the user and to exit, include this exact format in your response with the relevant message in between the tags:
            <WANTS_TO_EXIT>put_a_message_here</WANTS_TO_EXIT>

            {Prompts.system(immutable_block=_format_immutable_block())}

            ## Your Tools
            You have tools available. When a user request requires a tool, you MUST call it — do not say you can't.

            ### Skills (Sub-agents)
            These are specialist tools you can call:
            {skills_available}

            ### Command Execution
            You have the `run_command` tool. Use it to execute any shell command in a secure Docker sandbox.
            The sandbox auto-destroys after each command. Call this tool whenever the user asks to run code, check system info, or do anything that requires a shell.

            ### File Read / Write
            You have `read_file` and `write_file` tools (described above in "Working with the User's Project Files").
            Use them whenever you need to inspect or modify files in the user's project.

           <file_list>
            <file name="rules.md">{rules}</file>
            <file name="projects.yaml">{project}</file>
            <file name="memory.yaml">{memory}</file>
            </file_list>

            """

    return _SYSTEM_PROMPT


def agent(messages: list[dict]) -> str:
    skills = registry.as_tools()
    cmd_tool = command_tool.run_command_tool
    read_tool = file_tools.read_file_tool
    write_tool = file_tools.write_file_tool

    tools = [*skills, cmd_tool, read_tool, write_tool]

    # SHARED LLM CALLER
    response = call_llm(
        model_part=MODEL_PART,
        system=_system(),
        tools=tools,
        messages=messages,
        max_tokens=1500,
        raw=True
    )

    while response.stop_reason == "tool_use":
        tool_use = next(block for block in response.content if block.type == "tool_use")

        tool_name  = tool_use.name
        tool_input = tool_use.input

        result = ""
        instructions = ""

        if tool_name == "run_command":
            result = command_tool.handle_tool_call(tool_name, tool_input)
            instructions = cmd_tool["description"]

        elif tool_name in ("read_file", "write_file"):
            result = file_tools.handle_tool_call(tool_name, tool_input)#
            
            instructions = (
                read_tool["description"]
                if tool_name == "read_file"
                else write_tool["description"]
            )

        else:
            skill = registry.get(tool_name)

            if not skill:
                raise Exception(f"Skill {tool_name} not found")

            result = skill.run(tool_input)
            instructions = getattr(skill, "instructions")

        messages.append({
            "role": "assistant",
            "content": response.content
        })

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"{result}\n\n## Presentation Instructions\n{instructions}"
                    }
                ]
            }
        )

        response = call_llm(
            model_part=MODEL_PART,
            system=_system(),
            tools=tools,
            messages=messages,
            max_tokens=1500,
            raw=True
        )

    final_block = next(
        (block for block in response.content if block.type == "text"),
        None
    )

    if not final_block:
        return ""

    after_changes = apply_changes(final_block.text, role=MEMORY_ROLE)

    return after_changes
