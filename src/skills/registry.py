# Sub agent skills
from src.skills.slop_detector.skill import SlopDetectorSkill



class SkillRegistry:
    def __init__(self):
        self.skills = [
            SlopDetectorSkill(),
            # We can now just add new skills here
        ]

    def match(self, data) -> "Skill | None":
        for skill in self.skills:

            if skill.triggered_by(data):
                return skill

        return None

registry = SkillRegistry()

