from src.utils.base_loop import run_loop
from src.agent.llm import agent


def run_agent():
    run_loop(
        title="CORE AGENT",
        input_prompt="Ask something",
        llm_fn=agent,
        verify_always=False,
    )

    