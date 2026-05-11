import logging

logger = logging.getLogger(__name__)

import subprocess
import uuid
import os
import shutil

from tools.resolve.resolve_result import ResolveResult
from tools.command.create_sandbox import IMAGE_NAME, build_sandbox_image
from get_root import root

# Absolute path resolution guarantees the mount works regardless of where the script is called
# WORKSPACE_PATH = Path(__file__).resolve().parent.parent.parent / "workspace"
WORKSPACE_PATH = (root.project) / "workspace"
DOCKER_BIN = shutil.which("docker")

def run_command(command: str, timeout: int = 30) -> dict:
    if not DOCKER_BIN:
        system_error="System Error: Docker executable not found."
        logger.error(system_error)
        return ResolveResult(
            success=False,
            error={
                "stdout": "",
                "stderr": system_error,
                "exit_code": 1,
                "success": False
            }
        )

    build_sandbox_image()

    container_name = f"vraksha-exec-{uuid.uuid4().hex[:8]}"
    uid = os.getuid()
    gid = os.getgid()

    docker_cmd = [
        DOCKER_BIN, "run",
        "--rm",                                     # Auto-destroy
        "--name", container_name,
        "--network", "none",                        # Air-gapped
        "--memory", "512m",                         # Resource limit
        "--cpus", "1.0",                            # CPU limit
        "-v", f"{WORKSPACE_PATH}:/workspace",       # Workspace mapping
        "-w", "/workspace",                         # Start in workspace
        "-u", f"{uid}:{gid}",                       # Host user mapping for safe file persistence
        IMAGE_NAME,
        "sh", "-c", command
    ]

    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        stdout_result=result.stdout
        logger.info(f"Result from stdout: {stdout_result}")
        return ResolveResult(
            success=True,
            result={
                "stdout": stdout_result,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
        )

    except subprocess.TimeoutExpired:
        # Force kill the container if the process hangs (e.g., waiting for interactive input)
        subprocess.run([DOCKER_BIN, "rm", "-f", container_name], capture_output=True)
        time_out_error=f"Error: Command timed out after {timeout} seconds."
        return ResolveResult(
            success=True,
            result={
                "stdout": "", 
                "stderr": time_out_error, 
                "exit_code": 124, 
                "success": False
            }
        )
    except Exception as e:
        logger.error(str(e))
        return ResolveResult(
            success=True,
            result={
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "success": False
            })
