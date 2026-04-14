import requests
from src.skills.slop_detector.services.github_token import get_token

API_BASE = "https://api.github.com"
RAW_BASE = "https://raw.githubusercontent.com"

EXTENSIONS_TO_SKIP = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".mp3", ".bin", ".exe", ".lock",
}

def _headers():
    return {
        "Authorization": f"Bearer {get_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def fetch_default_branch(owner: str, repo: str) -> str:
    url = f"{API_BASE}/repos/{owner}/{repo}"
    res = requests.get(url, headers=_headers())

    return res.json().get("default_branch", "main")


def fetch_repo_tree(owner: str, repo: str, branch: str) -> list[dict]:
    url = f"{API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    res = requests.get(url, headers=_headers())

    if res.status_code != 200:
        return []

    return res.json().get("tree", [])


def fetch_raw_file(owner: str, repo: str, branch: str, path: str, max_bytes: int = 512000, max_chars: int = None) -> str | None:
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""

    if ext in EXTENSIONS_TO_SKIP:
        return None

    url = f"{RAW_BASE}/{owner}/{repo}/{branch}/{path}"
    res = requests.get(url, headers=_headers(), timeout=10)
    
    if res.status_code != 200:
        return None

    if len(res.content) > max_bytes:
        return None

    if max_chars:
        return res.text[:max_chars]
    else:
        return res.text


def fetch_file_via_contents_api(owner: str, repo: str, path: str, branch: str, max_chars: int=None) -> dict | None:
    import base64

    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    res = requests.get(url, headers=_headers())

    if res.status_code != 200:
        return None

    data = res.json()

    # Files >1MB won't have content field so fall back to raw
    if "content" not in data:
        if max_chars:
            content = fetch_raw_file(owner, repo, branch, path, max_chars=max_chars)
        else:
            content = fetch_raw_file(owner, repo, branch, path)
    else:
        if max_chars:
            content = base64.b64decode(
                data["content"].replace("\n", "")
            ).decode("utf-8", errors="replace")[:max_chars]
        else:
            content = base64.b64decode(
                data["content"].replace("\n", "")
            ).decode("utf-8", errors="replace")

    return {
        "path": data.get("path"),
        "size": data.get("size"),
        "sha": data.get("sha"),
        "content": content,
    }

    