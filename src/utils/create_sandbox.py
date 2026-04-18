import subprocess
import uuid

import logging

logger = logging.getLogger(__name__)

IMAGE_NAME = "vraksha-sandbox:latest"

def build_sandbox_image(dockerfile_path: str = "."):
    result = subprocess.run(
        ["docker", "build", "-t", IMAGE_NAME, dockerfile_path],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Image build failed:\n{result.stderr}")
        
    logger.info("Sandbox image ready.")


