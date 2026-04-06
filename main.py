# Agent is present in:
# "src/agent/loop.py"


# Slop detector to detect ai slop code vs human is present in:
# "src/slop_detector/loop.py"

import io
import sys

from src.agent.loop import run_agent

from src.slop_detector.loop import run_detector

# from src.utils.prepare_for_llm import PrepareForLLM

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if __name__ == "__main__":

    run_detector()