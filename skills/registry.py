import logging

logger = logging.getLogger(__name__)

from skills.registrar import register_skills
from skills.base import Skill

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
            logger.info(f"✅ Loaded skill: {skill.name}")

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
        return self.skills.get(name)

skill_registry = SkillRegistry()

