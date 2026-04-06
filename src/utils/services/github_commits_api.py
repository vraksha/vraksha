import requests
from src.utils.services.github_token import get_token
from src.utils.services.url_parser import parse


def _headers():
    return {
        "Authorization": f"Bearer {get_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def fetch_commit_list(owner: str, repo: str, per_page: int = 20) -> list[dict] | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    res = requests.get(url, headers=_headers(), params={"per_page": per_page})
    
    return res.json() if res.status_code == 200 else None


def fetch_commit_detail(owner: str, repo: str, sha: str) -> dict | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    res = requests.get(url, headers=_headers())

    print(res.status_code, res.text[:200])

    if res.status_code != 200:
        return None

    data = res.json()

    return {
        "files": [
            {
                "filename": f["filename"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "changes": f["changes"]
            }
            for f in data.get("files", [])
        ]
    }

    