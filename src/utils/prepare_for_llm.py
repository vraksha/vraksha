from src.utils.user_input import UserInput
from src.utils.services.fetch_commits import get_commits
from src.utils.services.fetch_content import get_content


class PrepareForLLM:
    
    @classmethod
    def get_data(cls, messages: list[dict]) -> dict:
        current_prompt = messages[-1]["content"] if messages else ""
        
        data = UserInput(raw_text=current_prompt)
        
        content = None
        commits = None
        
        if data.url:
            url = str(data.url)
            content = get_content(url)
            commits = get_commits(url)
            return {
                "url": url,
                "content": content,
                "commits": commits,
                "prompt": data.prompt,
            }
        
        return {
            "url": None,
            "content": None,
            "commits": None,
            "prompt": current_prompt,
        }
            