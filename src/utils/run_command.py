import subprocess
import uuid

from src.utils.create_sandbox import IMAGE_NAME, build_sandbox_image

_image_ready = False

def _ensure_image():
    global _image_ready
    if not _image_ready:
        build_sandbox_image()
        _image_ready = True

def run_command(command: str, timeout: int = 30) -> dict:
    """
    To give ability to vraksha to run a shell command in a freah and isolated docker container.

    The container will automatically be destroyed after execution.
    
    This is done to ensure security and prevent any harm to the host system.
    """

    _ensure_image()

    container_name = f"sandbox-{uuid.uuid4().hex[:8]}"

    try:
        result = subprocess.run(
            [
                "docker", "run",
                "--rm",                          # auto-destroy on exit
                "--name", container_name,
                "--network", "none",             # no internet access
                "--memory", "256m",              # memory cap
                "--cpus", "0.5",                 # CPU cap
                "--read-only",                   # read-only filesystem
                "--tmpfs", "/tmp",               # writable temp dir
                IMAGE_NAME,
                "sh", "-c", command
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "success": result.returncode == 0
        }

    except subprocess.TimeoutExpired:
        # We have to kill the container if it times out
        subprocess.run(["docker", "kill", container_name], capture_output=True)
        return {"stdout": "", "stderr": "Timed out", "exit_code": -1, "success": False}

