import logging
from src.agent.loop import run_agent

# Use 'a' to append or 'w' to overwrite every time you restart
logging.basicConfig(
    filename="vraksha.log",
    filemode="a", 
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Keep the noise from external libraries down
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("docker").setLevel(logging.WARNING) # Add this to quiet Docker logs

logger = logging.getLogger(__name__)
logger.info("--- Vraksha Session Started ---")