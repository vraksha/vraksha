from abc import ABC, abstractmethod

class Tool(ABC):
    name: str
    action: str
    description: str
    input_schema: dict = {
        "type": "object",
        "properties": {},
        "required": []
    }

    @abstractmethod
    def call(self, tool_input: dict) -> str:
        pass

