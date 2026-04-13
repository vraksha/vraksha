from src.skills.base import Skill
from src.skills.slop_detector.llm import detector_agent

class SlopDetectorSkill(Skill):
    name = "slop_detector"
    description = "Analyzes GitHub repos for AI-generated code forensics."
    instructions = ""
    input_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "GitHub repo URL to analyze"},
            "user_prompt": {"type": "string", "description": "Original user message"}
        },
        "required": ["url"]
    }

    def run(self, tool_input: dict) -> str:
        repo_url = tool_input.get("url", "")
        user_prompt = tool_input.get("user_prompt", "analyze this repo")
        
        messages = [{"role": "user", "content": f"{user_prompt}\n{repo_url}"}]

        return detector_agent(messages)

def get_skill() -> Skill:
    return SlopDetectorSkill()

