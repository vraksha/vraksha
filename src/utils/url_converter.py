from urllib.parse import urlparse


def manipulate(repo_url: str) -> str:
    parsed = urlparse(repo_url)
    parts = parsed.path.strip("/").split("/")

    owner = parts[0]
    repo = parts[1]
    filepath = "/".join(parts[4:]) if len(parts) > 4 else ""

    return f"https://api.github.com/repos/{owner}/{repo}/contents/{filepath}"

    