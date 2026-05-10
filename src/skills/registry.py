import logging

logger = logging.getLogger(__name__)


from src.skills.registrar import register_skills
from src.skills.base import Skill

class SkillRegistry:
    def __init__(self):
        self.skills: dict[str, Skill] = {}
        self._load()

    def _load(self):
        for entry in register_skills():
            module = entry["module"]
            if not hasattr(module, "get_skill"):
                continue

            skill = module.get_skill()
            
            if entry["instruction_path"]:
                skill.instructions = entry["instruction_path"].read_text(encoding="utf-8")
            else:
                skill.instructions = "No specific instructions provided."

            self.skills[skill.name] = skill

    def as_skills(self) -> list[dict]:
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "input_schema": skill.input_schema
            }
            for skill in self.skills.values()
        ]

    def get(self, name: str) -> "Skill | None":
        return next((s for s in self.skills if s.name == name), None)

skill_registry = SkillRegistry()

