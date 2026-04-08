# Necessary packages
from rich.console import Console

# Custom modules
from src.agent.prompts import Prompts
from src.utils.read_memory import extract_content
from src.utils.changes import apply_changes

from src.skills.slop_detector.services.user_input import UserInput

# Skills registrations
from src.utils.client import client_info
from src.skills.registry import registry

# Shared llm caller
from src.utils.call_llm import call_llm

# Sub Agent skills
from src.skills.slop_detector.llm import detector_agent


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
        f"- {skill.name}: {skill.description}\n{skill.instruction}"
        for skill in registry.skills
    )

    _SYSTEM_PROMPT = f"""
            {Prompts.system()}

            ## Available Skills
            You have access to the following specialist skills.
            When the input matches a skill, it will be automatically routed — you just explain the result.
            {skills_available}

           <file_list>
            <file name="rules.md">{rules}</file>
            <file name="projects.yaml">{project}</file>
            <file name="memory.yaml">{memory}</file>
            </file_list>
            
            """

    return _SYSTEM_PROMPT


def agent(messages: list[dict]) -> str:
    current_prompt = messages[-1]["content"] if messages else ""
        
    data = UserInput(raw_text=current_prompt)

    # We check if there are any skills available to handle current request
    skill = registry.match(data)

    if skill:
        console.log(f"[yellow]Skill matched: {skill.name}[/yellow]")
        detector_verdict = skill.run(messages)

        messages[-1]["content"] = (
            f"USER ORIGINAL REQUEST: {current_prompt}\n\n" # Keep their context!
            f"--- INTERNAL FORENSIC REPORT BY '{skill.name.upper()}'---\n{detector_verdict}\n"
                "--- INSTRUCTION ---\n"
                "Explain the report above to the user based on their original request."
            )

        console.log(f"[bold magenta]DEBUG Specialist Output:[/bold magenta] {detector_verdict[:100]}...")

    # SHARED LLM CALLER
    response = call_llm(
        role=ROLE,
        system=_system(),
        messages=messages,
        max_tokens=1500
    )

    apply_changes(response, part=PART)

    return response

