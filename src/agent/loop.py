
from src.agent.llm import call_llm

def run_agent():
    messages = []

    while True:
        print("\n======================================================================================")
        print("=                                                                                      =")
        print("============= Enter 'quit' or 'exit' or 'bye' or 'q' or 'e' or 'b' to exit =============")
        print("=                                                                                      =")
        print("======================================================================================\n")

        prompt = input("Ask something:\n")

        if prompt.lower() in ["quit", "exit", "bye", "q", "e", "b"]:
            
            messages.append({
                "role": "user",
                "content": "Session ending.. Rewrite memory.yaml with a clean compressed summary of everything discussed this session. Update projects.yaml if anything changed."
                })

            print(call_llm(messages))
            break

        messages.append({
        "role": "user",
        "content": prompt
    })
        
        response_text = call_llm(messages)

        messages.append({
        "role": "assistant",
        "content": response_text
    })

        print(f"\nAgent:\n{response_text}")

        print("\n======================================================================================\n")

