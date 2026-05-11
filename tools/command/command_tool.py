import logging

logger = logging.getLogger(__name__)

from tools.command.run_command import run_command

class CommandTool:
    def __init__(self):
        self.run_command_tool = {
            "name": "run_command",
            "description": "Run a shell command in a secure, isolated sandbox. Auto-destroys after use.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Max seconds to wait (default 30)",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        }

    def handle_tool_call(self, tool_input: dict) -> str:
        command = tool_input["command"]
        timeout = tool_input.get("timeout", 30)
        
        result = run_command(command=command, timeout=timeout)
        logger.info(f"Result '{result}' from command '{command}'")
        
        # To prevent Context Window Explosion
        # If the output is over ~2500 chars, we truncate it so the LLM doesn't crash.
        MAX_CHARS = 2500
        
        stdout = result['stdout']
        if len(stdout) > MAX_CHARS:
            stdout = stdout[:MAX_CHARS] + f"\n... [TRUNCATED: Output exceeded {MAX_CHARS} characters]"
            
        stderr = result['stderr']
        if len(stderr) > MAX_CHARS:
            stderr = stderr[:MAX_CHARS] + f"\n... [TRUNCATED: Error exceeded {MAX_CHARS} characters]"

        # Format clearly for the LLM
        output = f"Exit code: {result['exit_code']}\n"
        
        if stdout.strip():
            output += f"stdout:\n{stdout}\n"
        if stderr.strip():
            output += f"stderr:\n{stderr}\n"
            
        final = output.strip()

        logger.info(final)
        return final

command_tool = CommandTool()