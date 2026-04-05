import requests

from src.utils.github_token import get_token

def get_commits(repo_url: str) -> list[dict]:
    token = get_token()

    commit_url = f"{repo_url.rstrip('/')}/commits"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vd.github+json",
        "X-Github-Api-Version": "2022-11-28"
    }

    res = requests.get(commit_url, headers=headers)

    if res.status_code == 200:
        return res.json()

    else:
        return f"Error: {res.status_code} - {res.text}"

