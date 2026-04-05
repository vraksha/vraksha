from urllib.parse import urlparse


def manipulate(repo_url: str) -> str:
    """
    Converts a GitHub URL to a GitHub API URL.

    e.g. https://github.com/owner/repo/blob/branch/path/to/file
      -> https://api.github.com/repos/owner/repo/contents/path/to/file
    """
    parsed = urlparse(repo_url)
    # parsed.path => /owner/repo/blob/branch/path/to/file
    parts = parsed.path.strip("/").split("/")

    owner = parts[0]
    repo = parts[1]
    # parts[2] is "blob" or "tree", parts[3] is branch — we just skip both
    filepath = "/".join(parts[4:]) if len(parts) > 4 else ""

    return f"https://api.github.com/repos/{owner}/{repo}/contents/{filepath}"

    