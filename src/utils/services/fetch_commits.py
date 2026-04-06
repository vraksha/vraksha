from statistics import median
from datetime import datetime

from src.utils.services.url_parser import parse
from src.utils.services.github_commits_api import fetch_commit_list, fetch_commit_detail


def get_commits(url: str) -> dict | None:
    info = parse(url)
    owner, repo = info["owner"], info["repo"]

    raw = fetch_commit_list(owner, repo)
    if not raw:
        return None

    messages = []
    timestamps = []
    total_additions = 0
    total_deletions = 0
    files_changed = set()

    for c in raw:
        sha = c["sha"]
        commit = c["commit"]

        messages.append(commit["message"])
        timestamps.append(commit["author"]["date"])

        detail = fetch_commit_detail(owner, repo, sha)
        
        if detail:
            for f in detail["files"]:
                total_additions += f["additions"]
                total_deletions += f["deletions"]
                files_changed.add(f["filename"])

    # Burst rate + median interval
    parsed_times = sorted([
        datetime.fromisoformat(t.replace("Z", "+00:00")) for t in timestamps
    ])

    intervals = [
        (parsed_times[i] - parsed_times[i - 1]).total_seconds()
        for i in range(1, len(parsed_times))
    ]

    total_minutes = (
        (parsed_times[0] - parsed_times[-1]).total_seconds() / 60
        if len(parsed_times) >= 2 else 0
    )

    return {
        "burst_rate": {
            "commits": len(raw),
            "over_minutes": round(total_minutes, 2)
        },

        "median_interval_seconds": round(median(intervals), 2) if intervals else None,

        "churn": {
            "additions": total_additions,
            "deletions": total_deletions,
            "files_changed": len(files_changed)
        },
        
        "commit_messages": messages
    }

    