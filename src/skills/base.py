from abc import ABC, abstractmethod

class Skill(ABC):
    name: str
    description: str        # Injected this into orchestrator system prompt
    instruction: str        # Loaded from SKILL.md

    @abstractmethod
    def triggered_by(self, data) -> bool:
        """Does this skill handle this input?"""
        pass

    @abstractmethod
    def run(self, messages: list[dict]) -> str:
        """Execute and return result string."""
        pass
        