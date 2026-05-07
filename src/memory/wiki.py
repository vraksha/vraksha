import os
from pathlib import Path

from get_root import root

ROOT = root.project
WIKI_PATH = ROOT / "memory" / "wiki"

def _check_wiki_path():
    WIKI_PATH.mkdir(parents=True, exist_ok=True)

_check_wiki_path()


def load_wiki(filename: str = "wiki_test") -> str:
    """
        Check for the given filename and return the content if it exists
    """
    filename = Path(filename)

    if filename.suffix != ".md":

        filename = filename.with_suffix(".md")

    try:
        path = WIKI_PATH / filename

        if not path.exists():
            return ""

        return path.read_text(encoding="utf-8")

    except OSError as e:
        raise Exception(f"Error occured while reading from wiki: {e}")


def write_wiki(text: str, filename: str) -> None:
    """
        Writing logic for the wiki
    """
    filename = Path(filename)

    if filename.suffix != ".md":
        filename = filename.with_suffix(".md")

    path = WIKI_PATH / filename
    
    try:
        if path.exists():
            with open(path, "a") as f:
                f.write(f"\n\n{text}")

        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    except OSError as e:
        raise Exception(f"Failed to write to wiki: {e}")
