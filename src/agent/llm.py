# Necessary packages
from rich.console import Console
import textwrap

# Custom modules
from src.agent.prompts import Prompts
from src.utils.read_file import extract_content
from src.utils.changes import apply_changes
from src.utils.immutables import immutable_paths

# Tools and commands
from src.utils.command_tool import command_tool

# Skills/tools registrations
from src.skills.registry import skill_registry
from src.tools.registry import tool_registry

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
    journal = extract_content(filename="journal",  role=MEMORY_ROLE)
    soul    = extract_content(filename="soul",     role=None) # Look in memory/ root

    skills_available = "\n".join(
        f"- {skill['name']}: {skill['description']}\n{skill.get('instructions', '')}"
        for skill in skill_registry.as_skills()
    )

    tools_available = "\n".join(
        f"- {tool['name']}: {tool['description']}"
        for tool in tool_registry.as_tools()
    )

    _SYSTEM_PROMPT = textwrap.dedent(f"""
        <identity>
        {soul}
        </identity>

        <journal>
        {journal}
        </journal>

        ## The Living Journal Protocol
        You maintain a living record of your user in 'memory/agent/journal.md'.
        If you learn something new about the user's preferences, identity, or how they want you to behave, update this file IMMEDIATELY using the 'write_file' tool.
        Do not wait for the end of the session.
        This file is your "brain" for the user's persona—keep it accurate and updated in real-time.

        {Prompts.system(immutable_block=_format_immutable_block())}

        ## Your Tools
        You have tools available.
        When you get response from user, think whether you can use the tool or not, if there's even a small chance you could use tool, you MUST CALL the tool.
        DONOT GIVE UP one the very first attempts, ask user for help only when you have failed multiple times.
        Try whatever you can before asking user for help.

        These are the tools you can call:
        {tools_available}

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
    """)

    return _SYSTEM_PROMPT

def agent(messages: list[dict]) -> str:
    system_prompt = _system()
    skills = skill_registry.as_skills()
    cmd_tool = command_tool.run_command_tool
    avail_tools = tool_registry.as_tools()
    all_tools_schemas = [cmd_tool, *skills, *avail_tools]

    response = call_llm(
        model_part=MODEL_PART,
        system=system_prompt, # Use the cached version
        tools=all_tools_schemas,
        messages=messages,
        max_tokens=1500,
        raw=True
    )

    while response.stop_reason == "tool_use":
        console.log('\n[muted]  • Thinking...[/muted]')
        
        messages.append({
            "role": "assistant",
            "content": response.content
            })

        tool_results = []

        for block in response.content:
            if block.type != "tool_use":
                continue
        
            tool_name = block.name
            tool_input = block.input
            result = ""

            if tool_name == "run_command":
                console.log(f'[muted]  • Executing Shell Command[/muted]')

                result = command_tool.handle_tool_call(tool_input)

            elif any(t["name"] == tool_name for t in avail_tools):
                tool = tool_registry.get(tool_name)

                console.log(f'[muted]  • {tool.action} [accent]{tool_input.get("path", "project")}[/accent][/muted]')
                
                result = tool.call(tool_input)

            elif any(t["name"] == tool_name for t in skills):
                skill = skill_registry.get(tool_name)

                
                console.log(f'[muted]  • Delegating to [accent]{tool_name}[/accent] skill[/muted]')
                result = skill.run(tool_input)
            
            else:
                result = f"Error: Tool {tool_name} not found in registry."
            
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result)
            })

        messages.append({"role": "user", "content": tool_results})

        response = call_llm(
            model_part=MODEL_PART,
            system=system_prompt, #Still using the cached system_prompt
            tools=all_tools_schemas,
            messages=messages,
            max_tokens=1500,
            raw=True
        )

    text_blocks = [b.text for b in response.content if b.type == "text"]
    final_text = "".join(text_blocks)

    if not final_text:
        return "Agent finished without a text response."

    processed_output = apply_changes(final_text, role=MEMORY_ROLE)
    
    return processed_output if isinstance(processed_output, str) else final_text
