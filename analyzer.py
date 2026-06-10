"""
analyzer.py — Sends repo data to Claude AI and gets structured analysis back
"""

import os
import json
import anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


SYSTEM_PROMPT = """You are RepoWise, an expert software engineer who analyzes GitHub repositories.
You produce clear, accurate, developer-friendly summaries that help engineers quickly understand a codebase before contributing.

Always respond ONLY with valid JSON (no markdown, no backticks, no extra text).

Your JSON must match this exact schema:
{
  "what_it_does": "2-3 sentence plain-English explanation of what this project does and who it's for",
  "tech_stack": ["list", "of", "key", "technologies", "frameworks", "languages"],
  "how_to_install": ["step 1", "step 2", "..."],
  "how_to_use": "Brief usage description with an example command or code snippet if available",
  "key_files": [
    {"file": "filename or path", "purpose": "what this file does"},
    ...
  ],
  "architecture_overview": "1-2 sentences describing project structure and design patterns used",
  "good_first_contribution": "Specific suggestion for where a new contributor could start",
  "caveats": "Any warnings, gotchas, or important notes (e.g. archived, alpha, requires API keys)",
  "one_liner": "One punchy sentence summarizing the project (like a tweet)"
}"""


def build_prompt(repo_data: dict, depth: str) -> str:
    """Build the analysis prompt from repo data."""
    
    file_summary = ""
    for fname, content in list(repo_data["file_contents"].items())[:8]:
        preview = content[:1500] if depth == "quick" else content[:3000]
        file_summary += f"\n\n--- {fname} ---\n{preview}"

    depth_instruction = {
        "quick": "Give a quick high-level summary. Depth is less important than speed.",
        "standard": "Give a thorough, accurate summary covering all schema fields well.",
        "deep": "Go deep. Infer architecture patterns, identify design decisions, and be highly specific about the codebase.",
    }.get(depth, "standard")

    return f"""Analyze this GitHub repository and return structured JSON.

{depth_instruction}

== REPO METADATA ==
Name: {repo_data['full_name']}
Description: {repo_data['description']}
Primary Language: {repo_data['language']}
All Languages: {json.dumps(repo_data['languages'])}
Stars: {repo_data['stars']} | Forks: {repo_data['forks']} | Open Issues: {repo_data['open_issues']}
Topics: {', '.join(repo_data['topics']) or 'none'}
License: {repo_data['license']}
Created: {repo_data['created_at']} | Last Updated: {repo_data['updated_at']}
Archived: {repo_data['archived']} | Is Fork: {repo_data['fork']}
Top Contributors: {', '.join(repo_data['contributors'][:5]) or 'unknown'}
Homepage: {repo_data['homepage'] or 'none'}

== FILE TREE (top-level) ==
{chr(10).join(repo_data['tree'][:50])}

== RECENT COMMIT MESSAGES ==
{chr(10).join(repo_data['recent_commits']) or 'none'}

== KEY FILE CONTENTS =={file_summary}

Now return the JSON analysis:"""


def analyze_repo(repo_data: dict, depth: str = "standard") -> dict:
    """Call Claude API to analyze the repo and return structured summary."""

    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Get your key at https://console.anthropic.com"
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = build_prompt(repo_data, depth)

    max_tokens = {"quick": 800, "standard": 1500, "deep": 2500}.get(depth, 1500)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI returned invalid JSON: {e}\n\nRaw response:\n{raw[:500]}")
