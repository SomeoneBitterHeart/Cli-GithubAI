#!/usr/bin/env python3
"""
RepoWise - AI-powered GitHub repo summarizer
Usage: python main.py <github_url>
"""

import typer
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from .fetcher import fetch_repo_data
from .analyzer import analyze_repo
from .renderer import render_summary

app = typer.Typer(
    help="🔍 RepoWise — Understand any GitHub repo in seconds using AI.",
    add_completion=False,
)
console = Console()


@app.command()
def summarize(
    repo_url: str = typer.Argument(..., help="GitHub repo URL (e.g. https://github.com/owner/repo)"),
    output: str = typer.Option("terminal", "--output", "-o", help="Output format: terminal | markdown | json"),
    depth: str = typer.Option("standard", "--depth", "-d", help="Analysis depth: quick | standard | deep"),
    save: str = typer.Option(None, "--save", "-s", help="Save output to file (e.g. summary.md)"),
):
    """Analyze a GitHub repository and generate an AI-powered structured summary."""

    console.print()
    console.print(Panel.fit(
        "[bold cyan]🔍 RepoWise[/bold cyan] [dim]— AI GitHub Repo Analyzer[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Fetch repo data
    with console.status(f"[cyan]Fetching repository data...[/cyan]"):
        try:
            repo_data = fetch_repo_data(repo_url)
        except Exception as e:
            console.print(f"[red]❌ Failed to fetch repo:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"[green]✓[/green] Fetched [bold]{repo_data['full_name']}[/bold] ({repo_data['language'] or 'unknown language'})")

    # Analyze with AI
    with console.status("[cyan]Analyzing with AI (this takes ~10s)...[/cyan]"):
        try:
            summary = analyze_repo(repo_data, depth=depth)
        except Exception as e:
            console.print(f"[red]❌ AI analysis failed:[/red] {e}")
            raise typer.Exit(1)

    console.print("[green]✓[/green] Analysis complete!\n")

    # Render output
    rendered = render_summary(summary, repo_data, fmt=output)

    if save:
        with open(save, "w") as f:
            f.write(rendered if output == "markdown" else _strip_ansi(rendered))
        console.print(f"\n[green]✓[/green] Saved to [bold]{save}[/bold]")
    else:
        console.print(rendered)


def _strip_ansi(text: str) -> str:
    import re
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def main():
    app()


if __name__ == "__main__":
    main()
