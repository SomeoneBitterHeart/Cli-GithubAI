"""
fetcher.py — Pulls all useful data from a GitHub repo via GitHub API + raw content
"""

import os
import re
import requests
from typing import Optional

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

IMPORTANT_FILES = [
    "README.md", "README.rst", "README.txt", "readme.md",
    "package.json", "pyproject.toml", "setup.py", "setup.cfg",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "requirements.txt", "Pipfile", "poetry.lock",
    "docker-compose.yml", "Dockerfile",
    "CONTRIBUTING.md", "CHANGELOG.md",
    ".github/workflows",
]

IMPORTANT_SOURCE_DIRS = ["src", "lib", "core", "app", "pkg", "internal"]


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def parse_repo_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from GitHub URL."""
    url = url.rstrip("/").replace(".git", "")
    patterns = [
        r"github\.com[:/]([^/]+)/([^/]+)",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1), m.group(2)
    raise ValueError(f"Cannot parse GitHub URL: {url}")


def fetch_repo_data(url: str) -> dict:
    """Fetch comprehensive repo metadata + key file contents."""
    owner, repo = parse_repo_url(url)

    # Core repo metadata
    r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=_headers(), timeout=15)
    if r.status_code == 404:
        raise ValueError(f"Repo not found: {owner}/{repo}")
    if r.status_code == 403:
        raise ValueError("GitHub API rate limit hit. Set GITHUB_TOKEN env var for higher limits.")
    r.raise_for_status()
    meta = r.json()

    # Languages breakdown
    lang_r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/languages", headers=_headers(), timeout=10)
    languages = lang_r.json() if lang_r.ok else {}

    # Top contributors
    contrib_r = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/contributors?per_page=5",
        headers=_headers(), timeout=10
    )
    contributors = [c["login"] for c in contrib_r.json()] if contrib_r.ok and isinstance(contrib_r.json(), list) else []

    # Repo file tree (top-level)
    tree_r = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/HEAD?recursive=0",
        headers=_headers(), timeout=10
    )
    tree = []
    if tree_r.ok:
        tree = [item["path"] for item in tree_r.json().get("tree", []) if item["type"] in ("blob", "tree")]

    # Fetch key file contents
    file_contents = {}
    default_branch = meta.get("default_branch", "main")

    files_to_fetch = _pick_files_to_fetch(tree)
    for filepath in files_to_fetch[:12]:  # cap at 12 files
        content = _fetch_file(owner, repo, filepath, default_branch)
        if content:
            file_contents[filepath] = content[:3000]  # truncate large files

    # Recent commits (last 5)
    commits_r = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/commits?per_page=5",
        headers=_headers(), timeout=10
    )
    recent_commits = []
    if commits_r.ok and isinstance(commits_r.json(), list):
        for c in commits_r.json():
            recent_commits.append(c["commit"]["message"].split("\n")[0])

    # Open issues / PRs count
    issues_r = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/issues?state=open&per_page=1",
        headers=_headers(), timeout=10
    )

    return {
        "url": url,
        "full_name": meta["full_name"],
        "description": meta.get("description") or "",
        "language": meta.get("language"),
        "languages": languages,
        "stars": meta.get("stargazers_count", 0),
        "forks": meta.get("forks_count", 0),
        "open_issues": meta.get("open_issues_count", 0),
        "topics": meta.get("topics", []),
        "license": (meta.get("license") or {}).get("name", "No license"),
        "created_at": meta.get("created_at", "")[:10],
        "updated_at": meta.get("updated_at", "")[:10],
        "default_branch": default_branch,
        "size_kb": meta.get("size", 0),
        "contributors": contributors,
        "tree": tree[:80],  # top-level file tree
        "file_contents": file_contents,
        "recent_commits": recent_commits,
        "homepage": meta.get("homepage") or "",
        "archived": meta.get("archived", False),
        "fork": meta.get("fork", False),
    }


def _pick_files_to_fetch(tree: list[str]) -> list[str]:
    """Intelligently pick which files are most useful to fetch."""
    priority = []
    # Always grab README first
    for f in ["README.md", "README.rst", "readme.md", "README.txt"]:
        if f in tree:
            priority.append(f)
            break

    # Config/manifest files
    for f in ["package.json", "pyproject.toml", "setup.py", "Cargo.toml",
              "go.mod", "pom.xml", "requirements.txt", "docker-compose.yml",
              "Dockerfile", "CONTRIBUTING.md", ".github/workflows"]:
        if f in tree and f not in priority:
            priority.append(f)

    # Main source entry points
    for f in tree:
        if any(f.endswith(ext) for ext in ["/main.py", "/index.js", "/main.go", "/main.rs", "/index.ts"]):
            priority.append(f)

    # Fill rest with .py/.js/.ts/.go source files from src/
    for f in tree:
        if f.startswith(("src/", "lib/", "core/", "app/")) and f not in priority:
            if any(f.endswith(ext) for ext in [".py", ".js", ".ts", ".go", ".rs"]):
                priority.append(f)

    return priority


def _fetch_file(owner: str, repo: str, path: str, branch: str) -> Optional[str]:
    """Fetch raw file content from GitHub."""
    try:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        r = requests.get(url, headers=_headers(), timeout=8)
        if r.ok and len(r.text) < 50_000:
            return r.text
    except Exception:
        pass
    return None
