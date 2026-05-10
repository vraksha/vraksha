import logging

from src.agent.loop import run_agent

logging.basicConfig(
    filename="vraksha.log",   
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logging.info("Application started")

def surprise_function():
    print("Hey you! 🎉 This isn't just a surprise — it's a whole celebration! 🌟 Whenever life throws a glitch your way, code your own path and dance it out!")

# AI Agent Note: This file was edited to demonstrate a Git commit.

if __name__ == "__main__":
    run_agent()
    surprise_function()

