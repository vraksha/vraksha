from src.utils.user_input import UserInput
from src.utils.services.fetch_commits import get_commits
from src.utils.services.fetch_content import get_content


class PrepareForLLM:
    @classmethod
    def get_data(cls, messages: list[dict]) -> dict:
        last_user_message = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            None
        )

        if not last_user_message:
            return {"url": None, "content": None, "commits": None, "prompt": None}

        data = UserInput(raw_text=last_user_message)

        content = None
        commits = None

        if data.url:
            url = str(data.url)
            content = get_content(url)
            commits = get_commits(url)

        return {
            "url": str(data.url) if data.url else None,
            "content": content,
            "commits": commits,
            "prompt": data.prompt,
        }

        