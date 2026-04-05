# Agent is present in:
# "src/agent/loop.py"


# Slop detector to detect ai slop code vs human is present in:
# "src/slop_detector/detector.py"

import io
import sys

from src.agent.loop import run

from src.utils.fetch_content import get_content

from src.slop_detector.detector import call_llm

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if __name__ == "__main__":
    print(call_llm("https://github.com/thecybro/AI-Agent"))