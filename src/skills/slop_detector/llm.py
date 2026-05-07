from src.skills.slop_detector.prompts import Prompts

from src.utils.read_file import extract_content
from src.utils.changes import apply_changes

from src.skills.slop_detector.services.prepare_for_llm import PrepareForLLM

from src.utils.call_llm import call_llm

MODEL_PART = "slop_detector" # For models.yaml key

def _forensic():

    _SYSTEM_PROMPT = f"""
        ## Behavior
        No URL yet → ask once. URL given earlier → use it, don't ask again.
        Code-only → analyze, flag lower confidence, don't harsh-verdict.
        If content and commits are None → repo is likely private, ask user.

        ## Task
        {Prompts.forensic()}

        ## Context
        (Sub-agents are focused on their specific task and do not manage memory)
        """
    return _SYSTEM_PROMPT

def detector_agent(messages: list[dict]) -> str:

    # All the data required for detector_agent
    data = PrepareForLLM.get_data(messages, max_chars=2000)

    content, commits, repo_url, prompt_only = (
        data["content"], data["commits"], data["url"], data["prompt"]
    )

    user_prompt = Prompts.analyze(
        user_prompt=prompt_only,
        repo_url=repo_url,
        repo_contents=content,
        commit_data=commits
    )

    history = messages[:-1] # Exclude the last message

    full_user_content = "\n\n".join(filter(None, [user_prompt]))

    ## Final message
    messages = history + [
        {
            "role": "user",
            "content": full_user_content
        }
    ]


    # SHARED LLM CALLER
    response = call_llm(
        model_part=MODEL_PART,
        system=_forensic(),
        messages=messages,
        max_tokens=1500
    )

    return response

