from src.memory.wiki import load_wiki, write_wiki

continue_commands = ["y"]

print("\n==================================")
decision = input("Wanna read and then write?\n")
print("==================================\n\n")


while decision.lower() in continue_commands:
    print("\n==================================")
    wiki_content = load_wiki(filename="WIKI")
    print(f"{wiki_content}\n")
    print("==================================\n\n")
    
    print("\n==================================")
    content = input("\nWhat do you wanna write to wiki?\n")
    write_wiki(content, "WIKI")

    print("\n==================================")
    print("Successfully wrote to wiki!\n" + f"\n{content}")
    print("==================================\n\n")

    print("\n==================================")
    decision = input("Wanna read and then write again?\n")
    print("==================================\n\n")

    if decision not in continue_commands:
        print("\nBye then!\n")