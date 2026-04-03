# Agent is present in:
# "src/agent/loop.py"


# Slop detector to detect ai slop code vs human is present in:
# "src/slop_detector/detector.py"

import io
import sys

from src.agent.loop import run

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if __name__ == "__main__":
    run()