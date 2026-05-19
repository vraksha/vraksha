"""
Sandbox runtime layer.

Responsible for:
- building sandbox image
- executing commands inside hardened container
- enforcing least privilege constraints
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

IMAGE_NAME = "vraksha-sandbox:latest"

DOCKER_BIN = shutil.which("docker")


# =========================================================
# Image build
# =========================================================

def build_sandbox_image(context_dir: str = ".", force: bool = False) -> None:
    """
    Build sandbox docker image if not present.
    """

    if not DOCKER_BIN:
        raise RuntimeError("Docker not found in PATH")

    # Skip build if exists
    if not force:
        exists = subprocess.run(
            [DOCKER_BIN, "images", "-q", IMAGE_NAME],
            capture_output=True,
            text=True,
        ).stdout.strip()

        if exists:
            logger.info("Sandbox image already exists")
            return

    logger.info("Building sandbox image...")

    subprocess.run(
        [DOCKER_BIN, "build", "-t", IMAGE_NAME, context_dir],
        check=True,
    )

    logger.info("Sandbox image ready")


# =========================================================
# Execution engine
# =========================================================

def execute_in_sandbox(command: str, timeout: int = 30) -> dict:
    """
    Execute shell command inside hardened sandbox.

    Returns STRICT JSON-like dict:
    {
        success: bool,
        data: {stdout, stderr, exit_code},
        error: str | None
    }
    """

    if not DOCKER_BIN:
        return {
            "success": False,
            "data": None,
            "error": "Docker not installed",
        }

    build_sandbox_image()

    container_id = f"agent-sbx-{uuid.uuid4().hex[:10]}"

    workspace = Path("workspace").resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    uid = os.getuid()
    gid = os.getgid()

    docker_cmd = [
        DOCKER_BIN,
        "run",
        "--rm",
        "--name", container_id,

        # =========================
        # HARD ISOLATION FLAGS
        # =========================
        "--network", "none",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",

        # resource limits
        "--memory", "512m",
        "--cpus", "1.0",
        "--pids-limit", "128",

        # filesystem
        "-v", f"{workspace}:/workspace",
        "-w", "/workspace",

        # user isolation (least privilege)
        "-u", f"{uid}:{gid}",

        IMAGE_NAME,
        "sh",
        "-c",
        command,
    ]

    try:
        proc = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": proc.returncode == 0,
            "data": {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
            },
            "error": None if proc.returncode == 0 else "Command failed",
        }

    except subprocess.TimeoutExpired:
        subprocess.run([DOCKER_BIN, "rm", "-f", container_id], capture_output=True)

        return {
            "success": False,
            "data": {
                "stdout": "",
                "stderr": f"Timeout after {timeout}s",
                "exit_code": 124,
            },
            "error": "Execution timeout",
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
        }

