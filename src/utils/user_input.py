import re
from typing import Any
from pydantic import BaseModel, HttpUrl, model_validator


class UserInput(BaseModel):
    raw_text: str
    url: str | None = None
    prompt: str | None = None

    @model_validator(mode='before')
    @classmethod
    def split_logic(cls, data: Any) -> Any:
        if isinstance(data, dict) and "raw_text" in data:
            text = data["raw_text"]

            url_match = re.search(r'(https?://\S+)', text)
            url = url_match.group(0) if url_match else None

            clean_prompt = text.replace(url, "").strip() if url else text.strip()

            data["url"] = url
            data["prompt"] = clean_prompt or None

        return data