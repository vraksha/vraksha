import os
import re
from pathlib import Path

import sys
import io

from anthropic import Anthropic

from extract_api import get_api_key
from prompts import Prompts
from extract_content import content_extractor
from changes import apply_changes

API_KEY = get_api_key(".env.local")

client = Anthropic(api_key=API_KEY)

# FORENSIC_PROMPT = Prompt.forensic()

# print(content_extractor(filename="rules"))

def call_llm(project, memory, rules):
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        system=f"""
            {Prompts.system()}

            <file_list>
                <file name="projects.yaml">
                    {project}
                </file>

                <file name="memory.yaml">
                    {memory}
                </file>

                <file name="rules.md">
                    {rules}
                </file>

            </file_list>
        """
        ,
        messages=[
            {
                "role": "user",
                "content": "Analyze the 3 given files and since now I know that what ysws submissions give to reviewers(which you don't need to know, so just proceed with updating if needed), update the relevant file with the text 'Will my agent perform good?' into relevant area of that file And update the date with today's date"
            }
            ],
    )

    response_text = response.content[0].text
    apply_changes(response_text)

    return(response_text)

project = content_extractor(filename="projects")
memory = content_extractor(filename="memory")
rules = content_extractor(filename="rules")


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print(call_llm(project, memory, rules))