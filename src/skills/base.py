from abc import ABC, abstractmethod

class Skill(ABC):
    name: str
    description: str
    instructions: str = ""
    input_schema: dict = {
        "type": "object",
        "properties": {}
    }

    @abstractmethod
    def call(self, tool_input: dict) -> str:
        pass

