import sys, io
from src.agent.prompts import Prompts
from src.utils.extract_content import content_extractor
from src.utils.changes import apply_changes

from src.utils.client import client_info

_SYSTEM_CACHE = None

def _system():
    global _SYSTEM_CACHE
    if _SYSTEM_CACHE:
        return _SYSTEM_CACHE

    # Getting the project, memory and rules
    rules = content_extractor(filename="rules")
    project = content_extractor(filename="projects")
    memory = content_extractor(filename="memory")

    _SYSTEM_CACHE = f"""
            {Prompts.system()}

            <file_list>
                <file name="rules.md">
                    {rules}
                </file>

                <file name="projects.yaml">
                    {project}
                </file>

                <file name="memory.yaml">
                    {memory}
                </file>


            </file_list>
        """

    return _SYSTEM_CACHE


def call_llm(messages) -> str:

    llm = client_info()

    client = llm["client"]
    client_name = llm["name"]
    model = llm["model"]

    response_text = None

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

    apply_changes(response_text)

    return response_text

