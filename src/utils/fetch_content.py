import requests
import base64
from urllib.parse import urlparse

from src.utils.url_converter import manipulate
from src.utils.github_token import get_token

TOKEN = get_token()

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_repo_tree(repo_url, branch="main"):
    path_parts = urlparse(repo_url).path.strip("/").split("/")

    if len(path_parts) < 2:
        raise ValueError("Invalid GitHub URL")

    owner, repo = path_parts[0], path_parts[1]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    
    res = requests.get(api_url, headers=headers)

    data = res.json()

    if isinstance(data, dict) and data.get("type") == "file":
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content

    if res.status_code != 200:
        if branch == "main":
            return get_repo_tree(repo_url, branch="master")

        raise Exception(f"Failed to fetch tree: {res.status_code}")

    return res.json().get("tree", []), owner, repo, branch

def get_content(repo_url):
    api_url = manipulate(repo_url)
    res = requests.get(api_url, headers=headers)

    if res.status_code != 200:
        raise Exception(f"Request failed: {res.status_code}")


    data = res.json()

    if isinstance(data, dict) and data.get("type") == "file":
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content

    tree, owner, repo, branch = get_repo_tree(repo_url)
    results = {}

    for item in tree:
        if item["type"] == "blob":
            file_path = item["path"]

            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
            
            file_res = requests.get(raw_url, headers=headers)
            
            if file_res.status_code == 200:
                results[file_path] = file_res.text
            else:
                print(f"Skipping {file_path}: {file_res.status_code}")

    return results

