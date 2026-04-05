import requests

from src.utils.github_token import get_token

def get_commit_details(path, sha, headers):
    url = f"https://api.github.com/repos/{path}/commits/{sha}"
    res = requests.get(url, headers=headers)

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


def get_commits(repo_url: str) -> list[dict]:
    token = get_token()
    path = repo_url.replace("https://github.com/", "").strip("/")

    api_url = f"https://api.github.com/repos/{path}/commits"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-Github-Api-Version": "2022-11-28"
    }

    params = {"per_page": 20}

    res = requests.get(api_url, headers=headers, params=params)

    if res.status_code != 200:
        return {"error": res.status_code, "message": res.text}

    raw_commits = res.json()
    final = []

    for c in raw_commits:
        commit_data = c["commit"]
        sha = c["sha"]

        base = {
            "sha": sha,
            "message": commit_data["message"],
            "author_name": commit_data["author"]["name"],
            "author_email": commit_data["author"]["email"],
            "date": commit_data["author"]["date"],
        }

        details = get_commit_details(path, sha, headers)

        if details:
            base.update(details)

        final.append(base)

    return final
