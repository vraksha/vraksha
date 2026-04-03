
def call_llm(user_prompt):
    
    import sys, io

    from anthropic import Anthropic

    from src.prompts import Prompts

    from src.utils.extract_api import get_api_key

    from src.utils.extract_content import content_extractor
    from src.utils.changes import apply_changes

    # Getting the api key
    API_KEY = get_api_key(".env.local")

    # Initializing the client
    client = Anthropic(api_key=API_KEY)

    # Getting the project, memory and rules
    project = content_extractor(filename="projects")
    memory = content_extractor(filename="memory")
    rules = content_extractor(filename="rules")

    # Calling the llm
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
                "content": user_prompt
            }
            ],
    )

    response_text = response.content[0].text
    apply_changes(response_text)

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    return response_text

