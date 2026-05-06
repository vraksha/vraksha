from pathlib import Path

WIKI_PATH = Path(__file__).parent.parent.parent / "memory/wiki/WIKI.md"

def load_wiki() -> str:
    if not WIKI_PATH.exists():
        return ""

    return WIKI_PATH.read_text(encoding="utf-8")
