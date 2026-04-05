import sys, io

from src.slop_detector.prompts import Prompts

from src.utils.changes import apply_changes
from src.utils.client import client_info
from src.utils.fetch_content import get_content
from src.utils.fetch_commits import get_commits

FORENSIC_PROMPT = Prompts.forensic()

def call_llm(repo_url) -> str:

    llm = client_info()

    client = llm["client"]
    client_name = llm["name"]
    model = llm["model"]

    content = get_content(repo_url)
    commits = get_commits(repo_url)

    user_prompt = Prompts.analyze(
                        repo_url=repo_url,
                        repo_contents=content,
                        commit_data=commits
                        )

    response_text = None

    # Calling the llm
    if client_name == "anthropic":
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=FORENSIC_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
        )

        response_text = response.content[0].text

    elif client_name == "openai":
        response = client.responses.create(
            model=model,
            max_output_tokens=1500,
            input=[
                {
                "role": "system",
                "content": FORENSIC_PROMPT
                },
                # conversation
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        response_text = response.output_text

    else:
        raise Exception("Couldn't get reponse from client")

    apply_changes(response_text)

    return response_text

