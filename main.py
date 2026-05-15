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

# This part was added by vraksha because it thought of suprising me, 
# but I commented it out for now
# def surprise_function():
    # logger.info("Hey you! 🎉 This isn't just a surprise — it's a whole celebration! 🌟 Whenever life throws a glitch your way, code your own path and dance it out!")

if __name__ == "__main__":
    try:
        run_agent()

    except KeyboardInterrupt:
        logger.info("Session interrupted by user.")

    except Exception as e:
        logger.exception(f"Fatal error during execution: {e}")
        
    finally:
        # surprise_function()
        logger.info("--- Vraksha Session Ended ---")
