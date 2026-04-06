from src.agent.prompts import Prompts
from src.utils.read_memory import extract_content_for_agent
from src.utils.changes import apply_changes

from src.utils.client import client_info

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

           <file_list>
            <file name="rules.md">{rules}</file>
            <file name="projects.yaml">{project}</file>
            <file name="memory.yaml">{memory}</file>
            </file_list>
            
            """

    return _SYSTEM_PROMPT


def call_llm(messages: list[dict]) -> str:

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

