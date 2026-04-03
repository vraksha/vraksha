from pathlib import Path
import re
from typing import Optional


def apply_changes(response_text: str, base=Path("memory")):
    """
    Parses LLM response for file update instructions and applies them
    to the target directory specified by `base`.

    Handles multiple response formats:
      - XML tags:   <file_update name="file.yaml">content</file_update>
      - Markdown:   **file.yaml:**  ```yaml\ncontent\n```
      - Labels:     Updated file.yaml:\n```yaml\ncontent\n```

    Args:
        response_text: The raw LLM response text.
        base: Target directory where changes are applied. Defaults to "memory".

    Returns:
        Number of files successfully updated.
    """
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)

    matched_files = {}

    # ── Strategy 1: XML-like <file_update> tags ──────────────────────────
    xml_pattern = r'<file_update\s+name="([^"]+?)">(.*?)</file_update>'
    for m in re.finditer(xml_pattern, response_text, re.DOTALL):
        name = m.group(1).strip()

        if _is_hardcoded(name):
            continue

        if _is_valid_filename(name):
            matched_files[name] = m.group(2).strip()

    # ── Strategy 2: <write_to_file><path>filename</path>content ────────────
    if not matched_files:
        wt_pattern = r'<write_to_file>\s*<path>([^<]+?)</path>(.*?)</write_to_file>'
        for m in re.finditer(wt_pattern, response_text, re.DOTALL):
            name = m.group(1).strip()
             
            if _is_hardcoded(name):
                continue
            
            if _is_valid_filename(name):
                matched_files[name] = m.group(2).strip()

    # ── Strategy 3: Filename label + fenced code block ───────────────────
    if not matched_files:
        block_pattern = r'```[\w]*\n(.*?)```'
        for block in re.finditer(block_pattern, response_text, re.DOTALL):
            # Grab a chunk of text before the code block to look for a filename
            start = max(0, block.start() - 300)
            preceding = response_text[start : block.start()]
            filename = _extract_filename(preceding, base)
             
            if _is_hardcoded(filename):
                continue
            
            if filename and filename not in matched_files:
                matched_files[filename] = block.group(1).strip()

    if not matched_files:
        print("⚠️ No valid file updates found in the LLM response.")
        return 0

    updates_applied = 0
    for filename, content in matched_files.items():
        filepath = base / filename
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Updated: {filepath}")
            updates_applied += 1
        except Exception as e:
            print(f"❌ Failed to write {filename}: {e}")

    if updates_applied == 0:
        print("⚠️ Matches found but all failed validation or writing.")

    return updates_applied


def _is_valid_filename(name: str) -> bool:
    """Check if a string looks like a valid filename."""
    return (
        bool(name)
        and " " not in name
        and len(name) <= 120
        and "\n" not in name
        and "." in name
    )


def _extract_filename(preceding_text: str, base: Path) -> Optional[str]:
    """
    Search text preceding a code block for a filename reference.
    Prefers filenames that match existing files in `base`.
    """
    # Collect known files from the target directory
    known_files = set()
    for f in base.rglob("*"):
        if f.is_file() and f.name != ".gitkeep":
            known_files.add(f.relative_to(base).as_posix())

    # Only look at the last few lines (closest to the code block)
    lines = preceding_text.rstrip().split("\n")
    search_area = "\n".join(lines[-4:])

    # Find all filename-like tokens (word.ext) in the search area
    fname_pattern = r'([a-zA-Z0-9_/.:-]+\.\w{1,10})'
    all_candidates = re.findall(fname_pattern, search_area)

    # Clean up each candidate (strip markdown bold markers, colons, etc.)
    cleaned = []
    for raw in all_candidates:
        c = raw.strip(":").strip("*").strip()
        if _is_valid_filename(c):
            cleaned.append(c)

    # Prefer a known file — take the last (closest) match
    for candidate in reversed(cleaned):
        if candidate in known_files:
            return candidate

    # Fallback: return the last valid filename-like candidate
    if cleaned:
        return cleaned[-1]

    return None

def _is_hardcoded(filename):
    if filename == "rules.md":
        print("⚠️ Changes can't be made in rules.md.")
        return True
    return False