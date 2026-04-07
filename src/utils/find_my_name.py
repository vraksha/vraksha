import re
from pathlib import Path

def my_name(base="memory", filename="rules.md") -> str:
    file = Path(base)/filename

    with open(file, "r") as f:
        content = f.read()

        match = re.search(r"Name:\s*(.*)", content)

        if match:
            return match.group(1).strip()

        return None