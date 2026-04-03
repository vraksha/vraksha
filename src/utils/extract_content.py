def content_extractor(base = "memory", filename=None) -> dict:
    from pathlib import Path

    base = Path(base)

    contents = {}

    for file in Path(base).iterdir():
        if (Path(base)/file).name == ".gitkeep":
            continue

        if file:
            with open(file) as f:
                name = file.stem
                contents[name] = f.read()

    return contents.get(filename, "File not found")

