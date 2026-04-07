from rich.console import Console

from src.agent.prompts import Prompts
from src.utils.read_memory import extract_content_for_agent
from src.utils.changes import apply_changes

from src.slop_detector.llm import detector_agent
from src.utils.user_input import UserInput

from src.utils.client import client_info

console = Console()

_SYSTEM_PROMPT = None

def _system():
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT:
        return _SYSTEM_PROMPT

    # Getting the project, memory and rules
    rules = extract_content_for_agent(filename="rules")
    project = extract_content_for_agent(filename="projects")
    memory = extract_content_for_agent(filename="memory")

    _SYSTEM_PROMPT = f"""
            {Prompts.system()}

            "If the user provides a GitHub URL, do NOT try to analyze it yourself.
            Instead, call the slop_detector tool. Use the output of that tool to provide your final answer."

            "When explaining a SLOP_DETECTOR report, you MUST conclude your response by asking the user to verify the verdict.
            Use a specific trigger phrase like 'VERIFICATION_REQUIRED' so the system knows to prompt for feedback."

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

    if data.url:
        with console.status("\n[bold yellow]Routing to Slop Detector specialist...\n", spinner="dots"):
            detector_verdict = detector_agent(messages)

            messages[-1]["content"] = (
                f"USER ORIGINAL REQUEST: {current_prompt}\n\n" # Keep their context!
                f"--- INTERNAL FORENSIC REPORT ---\n{detector_verdict}\n"
                "--- INSTRUCTION ---\n"
                "Explain the report above to the user based on their original request."
            )

        console.log(f"[bold magenta]DEBUG Specialist Output:[/bold magenta] {detector_verdict[:100]}...")

    llm = client_info()

    client = llm["client"]
    client_name = llm["name"]
    model = llm["model"]

    # Calling the llm
    if client_name == "anthropic":
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=_system(),
            messages=messages,
        )

        response_text = response.content[0].text

    elif client_name == "openai":
        response = client.responses.create(
            model=model,
            max_output_tokens=1500,
            input=[
                {
                "role": "system",
                "content": _system()
                },
                # conversation
                * messages
            ]
        )

        response_text = response.output_text

    else:
        raise Exception("Couldn't get reponse from client")

    apply_changes(response_text, part="agent")

    return response_text

