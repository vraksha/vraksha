import os
from pathlib import Path

import sys
import io

from anthropic import Anthropic

from extract_api import get_api_key
from forensic_prompt import forensic_prompt
from extract_content import content_extractor

API_KEY = get_api_key(".env.local")

client = Anthropic(api_key=API_KEY)

FORENSIC_PROMPT = forensic_prompt()

# print(content_extractor(filename="rules"))

def call_llm(extracted_content):
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        system=FORENSIC_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Analyze this file and answer in short, what's the current state of my latest project? {extracted_content}"
            }
            ],
    )

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print(response.content[0].text)

extracted_content = content_extractor(filename="projects")

call_llm(extracted_content)