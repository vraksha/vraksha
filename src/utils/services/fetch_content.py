from src.utils.services.url_parser import parse, classify

from src.utils.services.github_content_api import fetch_default_branch, fetch_repo_tree, fetch_raw_file, fetch_file_via_contents_api


def get_content(url: str) -> dict | None:
    info = parse(url)
    owner, repo = info["owner"], info["repo"]
    branch = info["branch"] or fetch_default_branch(owner, repo)

    if classify(url) == "file":
        return _get_file_content(owner, repo, branch, info["file_path"])

    return _get_repo_content(owner, repo, branch)


def _get_file_content(owner: str, repo: str, branch: str, path: str) -> dict | None:
    result = fetch_file_via_contents_api(owner, repo, path, branch)

    if not result:
        return None

    return {
        "type": "file",
        "path": result["path"],
        "size": result["size"],
        "sha": result["sha"],
        "content": result["content"]
    }


def _get_repo_content(owner: str, repo: str, branch: str) -> dict | None:
    tree = fetch_repo_tree(owner, repo, branch)

    if not tree:
        return None

    files = {}
    errors = {}

    for item in tree:
        if item["type"] != "blob":
            continue

        path = item["path"]
        content = fetch_raw_file(owner, repo, branch, path)

        if content is not None:
            files[path] = content
            
        else:
            errors[path] = "skipped or fetch failed"

    return {
        "type": "repo",
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "tree": [i["path"] for i in tree if i["type"] == "blob"],
        "files": files,
        "errors": errors
    }

    