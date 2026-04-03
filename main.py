import io
import sys

from src.llm import call_llm
from src.utils.changes import apply_changes

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

messages = []

while True:
    print("\n======= Enter 'quit' or 'exit' or 'bye' to exit =======\n")

    prompt = input("Ask something:\n")

    if prompt.lower() in ["quit", "exit", "bye"]:
        if len(messages) != 0:
            messages.append({
                "role": "user", "content": "Session ending. Rewrite memory.yaml with a clean compressed summary of everything discussed this session. Update projects.yaml if anything changed."
                })

            response_text = call_llm(messages)

        break

    messages.append({"role": "user", "content": prompt})
    
    response_text = call_llm(messages)

    messages.append({"role": "assistant", "content": response_text})

    print(f"\nAgent:\n{response_text}")

