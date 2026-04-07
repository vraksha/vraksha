import io
import sys

from src.agent.loop import run_agent # For general Agent

# from src.slop_detector.loop import run_detector # For AI slop detector 

from src.utils.prepare_for_llm import PrepareForLLM

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Now the general agent will call the slop detector by itself if it has to analyze github repo,
## User doesn't have to call slop detector specifically


if __name__ == "__main__":
    run_agent()
