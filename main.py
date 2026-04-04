# Agent is present in:
# "src/agent/loop.py"


# Slop detector to detect ai slop code vs human is present in:
# "src/slop_detector/detector.py"

import io
import sys

from src.agent.loop import run

from src.utils.fetcher import fetcher

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if __name__ == "__main__":
    print(fetcher("https://github.com/thecybro/AI-Agent/blob/main/main.py"))