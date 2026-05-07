from src.skills.slop_detector.prompts import Prompts

from src.utils.read_memory import extract_content
from src.utils.changes import apply_changes

from src.skills.slop_detector.services.prepare_for_llm import PrepareForLLM

from src.utils.call_llm import call_llm

"""Note that part for memory path is not used now"""
PART = "slop_detector" # For memory path
ROLE = "slop_detector" # For its function and client info

def _forensic():

    project = extract_content(filename="projects", part=PART)
    memory  = extract_content(filename="memory", part=PART)

    _SYSTEM_PROMPT = f"""
        ## Behavior
        No URL yet → ask once. URL given earlier → use it, don't ask again.
        Code-only → analyze, flag lower confidence, don't harsh-verdict.
        If content and commits are None → repo is likely private, ask user.

        ## Task
        {Prompts.forensic()}

        ## Memory Protocol
        Post-analysis, always append to projects.yaml:
        slop_analyses:
        - repo_url: url
            verdict: verdict
            probability_score: score
            confidence_reasoning: reasoning
            signals_found: [A1, A3, H2...]
            analyzed_at: date

        ## Context
        <file_list>
        <file name="projects.yaml">{project}</file>
        <file name="memory.yaml">{memory}</file>
        </file_list>
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
        role=ROLE,
        system=_forensic(),
        messages=messages,
        max_tokens=1500
    )

    """
        Apply changes for sub agents is removed because they will be designed to just do the task
        Orchestrator will handle everything else
    """
    # apply_changes(response, part=ROLE)

    return response

