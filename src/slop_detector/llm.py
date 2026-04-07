from src.slop_detector.prompts import Prompts

from src.utils.read_memory import extract_content_for_slop_detector
from src.utils.changes import apply_changes
from src.utils.client import client_info
from src.utils.prepare_for_llm import PrepareForLLM

_SYSTEM_PROMPT = None

def _forensic():
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT:
        return _SYSTEM_PROMPT

    rules   = extract_content_for_slop_detector(filename="rules")
    project = extract_content_for_slop_detector(filename="projects")
    memory  = extract_content_for_slop_detector(filename="memory")

    _SYSTEM_PROMPT = f"""
        No URL yet → ask once. URL given earlier → use it, don't ask again.
        Code-only (no commits/wakatime) → analyze, flag lower confidence, don't harsh-verdict.

        If you see content and commits as None, SUPPOSE that the repository or file is private and ask user to make it public or give another repo

        {Prompts.forensic()}

        ## Post-analysis: always append to projects.yaml
        slop_analyses:
        - repo_url: url
            verdict: verdict
            probability_score: score
            confidence_reasoning: reasoning
            signals_found: [list of triggered signal IDs e.g. A1,A3,H2]
            analyzed_at: date

        <file_list>
        <file name="rules.md">{rules}</file>
        <file name="projects.yaml">{project}</file>
        <file name="memory.yaml">{memory}</file>
        </file_list>
        """
    return _SYSTEM_PROMPT


def detector_agent(messages: list[dict]) -> str:
    llm = client_info()

    client, client_name, model = llm["client"], llm["name"], llm["model"]

    data = PrepareForLLM.get_data(messages)

    content, commits, repo_url, prompt_only = (
        data["content"], data["commits"], data["url"], data["prompt"]
    )

    user_prompt = Prompts.analyze(
        user_prompt=prompt_only,
        repo_url=repo_url,
        repo_contents=content,
        commit_data=commits
    )

    history = messages[:-1]

    full_user_content = "\n\n".join(filter(None, [user_prompt]))

    if client_name == "anthropic":
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=_forensic(),
            messages=
            history + [
                {
                    "role": "user",
                    "content": full_user_content
                }
            ]
        )

        response_text = response.content[0].text

    elif client_name == "openai":
        response = client.responses.create(
            model=model,
            max_output_tokens=1500,
            input=[
                {
                    "role": "system",
                    "content": _forensic()
                },
                messages + [
                    {
                        "role": "user",
                        "content": full_user_content
                    }
                ]
            ]
        )

        response_text = response.output_text

    else:
        raise Exception("Couldn't get response from client")

    apply_changes(response_text, part="slop_detector")

    return response_text

