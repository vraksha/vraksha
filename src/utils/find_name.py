import re
from pathlib import Path

def _find(entity: str, base="memory", filename="rules.md") -> str:
    file = Path(base)/filename

    with open(Path(file), "r") as f:
        content = f.read()

        match = re.search(fr'{entity}:\s*(.*)', content)

        if match:
            return match.group(1).strip()

        return None

def agent_name():
    return _find("Agent")

def user_name():
    return _find("Name")

