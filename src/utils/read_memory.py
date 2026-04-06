from pathlib import Path


def _extract_content(subfolder: str, filename: str | None) -> str | dict:
    contents = {}

    rules = Path("memory") / "rules.md"
    base = Path("memory") / subfolder

    if not rules.exists():
        raise FileNotFoundError(f"rules.md not found at {rules}")

    if not base.exists():
        raise FileNotFoundError(f"Memory folder not found: {base}")

    with open(rules, "r") as f:
        contents["rules"] = f.read()

    for file in base.iterdir():
        if file.name == ".gitkeep" or not file.is_file():
            continue
            
        with open(file, "r") as f:
            contents[file.stem] = f.read()

    return contents.get(filename, "File not found") if filename else contents


def extract_content_for_agent(filename: str | None = None):
    return _extract_content("agent", filename)


def extract_content_for_slop_detector(filename: str | None = None):
    return _extract_content("slop_detector", filename)

