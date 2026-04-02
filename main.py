import os
from pathlib import Path

from anthropic import Anthropic

from extract_api import get_api_key
from forensic_prompt import forensic_prompt

API_KEY = get_api_key(".env.local")

client = Anthropic(api_key=API_KEY)

FORENSIC_PROMPT = forensic_prompt()

def file_content_extractor(path = Path("memory"), filename) -> dict:
    contents = []

    for file in path.iterdir():
        if (path/file).name == ".gitkeep":
            continue

        if file:
            with open(file) as f:
                name = file.stem
                contents.append({name:f.read()})

    return contents

print(file_content_extractor("rules"))

