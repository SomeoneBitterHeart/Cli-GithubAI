import os
import re
import time
import requests
from typing import Optional
from requests.exceptions import RequestException, Timeout, ConnectionError

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MAX_RETRIES = int(os.getenv("GITHUB_MAX_RETRIES", "3"))

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


def _retry_request(max_retries: int = 3, backoff_factor: float = 1.0):
    """Decorator for retrying requests with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (Timeout, ConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor * (2 ** attempt)
                        time.sleep(wait_time)
                except RequestException as e:
                    # For other request exceptions, don't retry
                    raise
            raise Timeout(f"Request failed after {max_retries} retries. Last error: {last_exception}")
        return wrapper
    return decorator


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


@_retry_request(max_retries=GITHUB_MAX_RETRIES, backoff_factor=1.0)
def _fetch_with_retry(url: str, headers: dict, timeout: int) -> requests.Response:
    """Internal function to fetch with retry logic."""
    return requests.get(url, headers=headers, timeout=timeout)


def fetch_repo_data(url: str) -> dict:
    """Fetch comprehensive repo metadata + key file contents."""
    try:
        owner, repo = parse_repo_url(url)
    except ValueError as e:
        raise ValueError(f"Invalid GitHub URL: {e}")

    # Core repo metadata
    try:
        r = _fetch_with_retry(f"{GITHUB_API}/repos/{owner}/{repo}", _headers(), 15)
    except Timeout as e:
        raise ValueError(f"Timeout fetching repo metadata: {e}")
    except ConnectionError as e:
        raise ValueError(f"Connection error fetching repo metadata: {e}")
    except RequestException as e:
        raise ValueError(f"Network error fetching repo metadata: {e}")
    
    if r.status_code == 404:
        raise ValueError(f"Repo not found: {owner}/{repo}")
    if r.status_code == 403:
        raise ValueError("GitHub API rate limit hit. Set GITHUB_TOKEN env var for higher limits.")
    if r.status_code >= 500:
        raise ValueError(f"GitHub API error (status {r.status_code}): {r.text}")
    r.raise_for_status()
    meta = r.json()

    # Languages breakdown
    try:
        lang_r = _fetch_with_retry(f"{GITHUB_API}/repos/{owner}/{repo}/languages", _headers(), 10)
        languages = lang_r.json() if lang_r.ok else {}
    except (Timeout, ConnectionError, RequestException):
        languages = {}

    # Top contributors
    try:
        contrib_r = _fetch_with_retry(
            f"{GITHUB_API}/repos/{owner}/{repo}/contributors?per_page=5",
            _headers(), 10
        )
        contributors = [c["login"] for c in contrib_r.json()] if contrib_r.ok and isinstance(contrib_r.json(), list) else []
    except (Timeout, ConnectionError, RequestException):
        contributors = []

    # Repo file tree (top-level)
    try:
        tree_r = _fetch_with_retry(
            f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/HEAD?recursive=0",
            _headers(), 10
        )
        tree = []
        if tree_r.ok:
            tree = [item["path"] for item in tree_r.json().get("tree", []) if item["type"] in ("blob", "tree")]
    except (Timeout, ConnectionError, RequestException):
        tree = []

    # Fetch key file contents
    file_contents = {}
    default_branch = meta.get("default_branch", "main")

    files_to_fetch = _pick_files_to_fetch(tree)
    for filepath in files_to_fetch[:12]:  # cap at 12 files
        content = _fetch_file(owner, repo, filepath, default_branch)
        if content:
            file_contents[filepath] = content[:3000]  # truncate large files

    # Recent commits (last 5)
    try:
        commits_r = _fetch_with_retry(
            f"{GITHUB_API}/repos/{owner}/{repo}/commits?per_page=5",
            _headers(), 10
        )
        recent_commits = []
        if commits_r.ok and isinstance(commits_r.json(), list):
            for c in commits_r.json():
                recent_commits.append(c["commit"]["message"].split("\n")[0])
    except (Timeout, ConnectionError, RequestException):
        recent_commits = []

    # Open issues / PRs count
    try:
        issues_r = _fetch_with_retry(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues?state=open&per_page=1",
            _headers(), 10
        )
    except (Timeout, ConnectionError, RequestException):
        issues_r = None

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
    """Fetch raw file content from GitHub with retry logic."""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            r = requests.get(url, headers=_headers(), timeout=8)
            if r.ok and len(r.text) < 50_000:
                return r.text
            elif r.status_code >= 500:
                # Server error, retry
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
        except (Timeout, ConnectionError):
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
        except Exception:
            pass
    return None
