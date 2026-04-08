import io
import sys

from src.agent.loop import run_agent # For general Agent
# from src.skills.slop_detector.loop import run_detector # For AI slop detector 
# from src.utils.base_loop import run_loop # For orchestrator
from src.skills.slop_detector.services.prepare_for_llm import PrepareForLLM

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Now the general agent will call the slop detector by itself if it has to analyze github repo,
## User doesn't have to call slop detector specifically


if __name__ == "__main__":
    run_agent()

