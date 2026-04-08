from pathlib import Path

from src.skills.base import Skill
from src.skills.slop_detector.llm import detector_agent

class SlopDetectorSkill(Skill):
    name = "slop_detector"
    description = "Analyzes GitHub repositories for AI-generated code forensics."
    instruction = Path(__file__).parent.joinpath("SKILL.md").read_text()

    def triggered_by(self, data) -> bool:
        return bool(data.url)

    def run(self, messages: list[dict]) -> str:
        return detector_agent(messages)

