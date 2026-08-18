"""
Mines git history for a repository: commits, authors, files touched,
and flags commits that look like bug fixes based on message heuristics.
"""
import os
import re
import shutil
from datetime import datetime, timezone
from git import Repo

BUGFIX_PATTERN = re.compile(
    r"\b(fix|bug|patch|hotfix|issue|crash|error|resolve)\b", re.IGNORECASE
)

CLONE_ROOT = os.getenv("REPO_CLONE_ROOT", "/tmp/ctm_repos")


def clone_repository(url: str, repo_name: str) -> str:
    """Clone (or reuse) a repo locally and return its local path."""
    os.makedirs(CLONE_ROOT, exist_ok=True)
    local_path = os.path.join(CLONE_ROOT, repo_name)

    if os.path.exists(local_path):
        shutil.rmtree(local_path)

    Repo.clone_from(url, local_path, depth=500)  # cap history depth for speed
    return local_path


def is_bugfix_message(message: str) -> bool:
    return bool(BUGFIX_PATTERN.search(message or ""))


def mine_commit_history(local_path: str):
    """
    Walk commit history and yield structured commit records.
    """
    repo = Repo(local_path)
    records = []

    for commit in repo.iter_commits("HEAD"):
        try:
            files_changed = list(commit.stats.files.keys())
            insertions = commit.stats.total.get("insertions", 0)
            deletions = commit.stats.total.get("deletions", 0)
        except Exception:
            files_changed, insertions, deletions = [], 0, 0

        records.append({
            "sha": commit.hexsha,
            "author": commit.author.name,
            "author_email": commit.author.email,
            "message": commit.message.strip(),
            "committed_at": datetime.fromtimestamp(
                commit.committed_date, tz=timezone.utc
            ),
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
            "is_bugfix": 1 if is_bugfix_message(commit.message) else 0,
        })

    return records


def commits_touching_file(records, file_path: str):
    return [r for r in records if file_path in r["files_changed"]]
