# Necessary packages
from rich.console import Console
import json

# Custom modules
from src.agent.prompts import Prompts
from src.utils.read_memory import extract_content
from src.utils.changes import apply_changes

from src.utils.command_tool import command_tool

# Skills registrations
from src.skills.registry import registry

# Shared llm caller
from src.utils.call_llm import call_llm

console = Console()


PART = "agent"           # For memory path
ROLE = "orchestrator"    # For its function and client info


_SYSTEM_PROMPT = None

def _system():
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT:
        return _SYSTEM_PROMPT

    # Getting the project, memory and rules
    rules = extract_content(filename="rules", part=PART)
    project = extract_content(filename="projects", part=PART)
    memory = extract_content(filename="memory", part=PART)


    skills_available = "\n".join(
        f"- {skill.name}: {skill.description}\n{skill.instructions}"
        for skill in registry.skills
    )

    _SYSTEM_PROMPT = f"""
            - If the user wants to exit or leave or end the conversation, say something to the user and to exit, include this exact format in your response with the relevant message in between the tags:
            <WANTS_TO_EXIT>put_a_message_here</WANTS_TO_EXIT>

            {Prompts.system()}

            ## Your Tools
            You have tools available. When a user request requires a tool, you MUST call it — do not say you can't.

            ### Skills (Sub-agents)
            These are specialist tools you can call:
            {skills_available}

            ### Command Execution
            You have the `run_command` tool. Use it to execute any shell command in a secure Docker sandbox.
            The sandbox auto-destroys after each command. Call this tool whenever the user asks to run code, check system info, or do anything that requires a shell.

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

    tools = [*skills, cmd_tool]

    # SHARED LLM CALLER
    response = call_llm(
        role=ROLE,
        system=_system(),
        tools=tools,
        messages=messages,
        max_tokens=1500,
        raw=True
    )

    while response.stop_reason == "tool_use":
        tool_use = next(block for block in response.content if block.type == "tool_use")

        tool_name = tool_use.name
        tool_input = tool_use.input

        result = ""

        if tool_name == "run_command":
            result = command_tool.handle_tool_call(tool_name, tool_input)

            instructions = cmd_tool["description"]

        else:
            skill = registry.get(tool_name)

            if not skill:
                raise Exception(f"Skill {tool_name} not found")

            else:
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
            role=ROLE,
            system=_system(),
            tools=tools,
            messages=messages,
            max_tokens=1500,
            raw=True
        )

        
    final_text = next(
        block for block in response.content if block.type == "text"
        )

    apply_changes(final_text.text, part=PART)

    return final_text.text

