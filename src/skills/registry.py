import logging

logger = logging.getLogger(__name__)


from src.skills.registrar import register_skills
from src.skills.base import Skill

class SkillRegistry:
    def __init__(self):
        self.skills: list[Skill] = []
        self._load()

    def _load(self):
        for entry in register_skills():
            module = entry["module"]
            instruction = entry["instruction"]

            if not hasattr(module, "get_skill"):
                logger.error(f"⚠️ Skipping {entry['name']} — no get_skill() found")
                continue

            skill: Skill = module.get_skill()
            skill.instructions = instruction
            self.skills.append(skill)
            logger.info(f"✅ Loaded skill: {skill.name}")

    def as_tools(self) -> list[dict]:
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "input_schema": skill.input_schema
            }
            for skill in self.skills
        ]

    def get(self, name: str) -> "Skill | None":
        return next((s for s in self.skills if s.name == name), None)

registry = SkillRegistry()

