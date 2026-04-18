from src.skills.slop_detector.services.user_input import UserInput
from src.skills.slop_detector.services.fetch_commits import get_commits
from src.skills.slop_detector.services.fetch_content import get_content

class PrepareForLLM:
    
    @classmethod
    def get_data(cls, messages: list[dict], max_chars: int = None) -> dict:
        current_prompt = messages[-1]["content"] if messages else ""
        
        data = UserInput(raw_text=current_prompt)
        
        content = None
        commits = None
        
        if data.url:
            url = str(data.url)
            content = get_content(url, max_chars=max_chars)
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
            