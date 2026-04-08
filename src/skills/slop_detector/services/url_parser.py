from urllib.parse import urlparse

def parse(url: str) -> dict:
    """
    Returns { owner, repo, branch, file_path } from any GitHub URL.
    branch and file_path are None for bare repo URLs.
    """
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]

    if "github.com" not in parsed.netloc:
        raise ValueError(f"Not a GitHub URL: '{url}'")
        
    if len(parts) < 2:
        raise ValueError(f"URL must include at least owner and repo: '{url}'")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")

    if len(parts) == 2:
        return {
            "owner": owner,
            "repo": repo,
            "branch": None,
            "file_path": None
            }

    if parts[2] == "blob" and len(parts) >= 5:
        return {
            "owner": owner,
            "repo": repo,
            "branch": parts[3],
            "file_path": "/".join(parts[4:])
            }

    if parts[2] == "tree":
        return {
            "owner": owner,
            "repo": repo,
            "branch": parts[3] if len(parts) > 3 else None,
            "file_path": None
            }

    raise ValueError(f"Unrecognised GitHub URL shape: '{url}'")


def classify(url: str) -> str:
    """Returns 'file' or 'repo'."""
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]

    if len(parts) >= 4 and parts[2] == "blob":
        return "file"
        
    if len(parts) == 2 or (len(parts) >= 3 and parts[2] == "tree"):
        return "repo"

    raise ValueError(f"Cannot classify URL: '{url}'")

    