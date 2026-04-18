from src.utils.run_command import run_command

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

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "run_command":
            result = run_command(
                command=tool_input["command"],
                timeout=tool_input.get("timeout", 30)
            )
            
            return (
                f"Exit code: {result['exit_code']}\n"
                f"stdout:\n{result['stdout']}\n"
                f"stderr:\n{result['stderr']}"
            )

command_tool = CommandTool()