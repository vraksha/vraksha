import logging

logger = logging.getLogger(__name__)

import subprocess
import shutil
# from pathlib import Path

IMAGE_NAME = "vraksha-sandbox:latest"

# Dynamically locate Docker to prevent FileNotFoundError in DooD environments
DOCKER_BIN = shutil.which("docker")

def image_exists(image_name: str) -> bool:
    """Check if the docker image is already present locally."""
    if not DOCKER_BIN:
        run_time_error=("Docker executable not found. Is the Docker daemon running and socket mounted")
        logger.error(run_time_error)
        raise RuntimeError(run_time_error)

    result = subprocess.run(
        [DOCKER_BIN, "images", "-q", image_name],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())

def build_sandbox_image(dockerfile_dir: str = ".", force: bool = False):
    """Builds the sandbox image if it doesn't exist."""
    if not DOCKER_BIN:
        run_time_error=("Docker executable not found. Cannot build sandbox.")
        logger.error(run_time_error)
        raise RuntimeError(run_time_error)

    if image_exists(IMAGE_NAME) and not force:
        logger.info(f"Existing sandbox image '{IMAGE_NAME}' found. Skipping build.")
        return

    logger.info(f"Building sandbox image: {IMAGE_NAME}...")
    
    try:
        # Standard output remains uncaptured so we can monitor build layers in the terminal
        subprocess.run(
            [DOCKER_BIN, "build", "-t", IMAGE_NAME, dockerfile_dir],
            check=True
        )
        logger.info("✅ Sandbox image built successfully.")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to build sandbox image: {e}")
        raise RuntimeError("Sandbox environment could not be initialized.") from e
