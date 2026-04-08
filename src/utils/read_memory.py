import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def _load_immutables():
    config_path = PROJECT_ROOT / "memory" / "IMMUTABLE.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f).get("IMMUTABLE")


def extract_content(filename: str = None, part: str = None, base_dir: str = "memory") -> str | dict:
    base = PROJECT_ROOT / base_dir
    
    if not base.exists():
        raise FileNotFoundError(f"Base folder '{base}' not found!")

    if part == "skills":
        raise ValueError("Specify a sub-skill folder (e.g., 'slop_detector')")

    if part == "agent":
        target_dir = base / "agent"
    elif part:
        target_dir = base / "skills" / part
    else:
        target_dir = base

    if not target_dir.exists():
        raise FileNotFoundError(f"Path '{target_dir}' does not exist.")

    contents = {}
    for file in target_dir.iterdir():
        if file.is_file() and file.name != ".gitkeep":
            with open(file, "r", encoding="utf-8") as f:
                file_content = f.read()

                contents[file.name] = file_content
                contents[file.stem] = file_content

    if filename:
        return contents.get(filename, f"File '{filename}' not found in {target_dir}")
    
    return contents

