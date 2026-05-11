import logging

# Use 'a' to append or 'w' to overwrite every time you restart
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("vraksha.log"),
        # logging.StreamHandler() # To send logs to the terminal console
    ]
)

# Keep the noise from external libraries down
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("docker").setLevel(logging.WARNING) # Add this to quiet Docker logs

logger = logging.getLogger(__name__)
logger.info("--- Vraksha Session Started ---")

from src.agent.loop import run_agent

def surprise_function():
    logger.info("Hey you! 🎉 This isn't just a surprise — it's a whole celebration! 🌟 Whenever life throws a glitch your way, code your own path and dance it out!")

# AI Agent Note: This file was edited to demonstrate a Git commit.

if __name__ == "__main__":
    run_agent()
    surprise_function()
