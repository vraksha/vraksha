import io
import sys

import logging

from src.agent.loop import run_agent

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logging.getLogger("httpx").setLevel(logging.WARNING)

if __name__ == "__main__":
    run_agent()

