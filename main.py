#!/usr/bin/env python3
"""
RepoWise - AI-powered GitHub repo summarizer
Usage: python main.py <github_url>
"""

import typer
import sys
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from .fetcher import fetch_repo_data
from .analyzer import analyze_repo
from .renderer import render_summary

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

    # Validate input parameters
    valid_outputs = ["terminal", "markdown", "json"]
    if output not in valid_outputs:
        console.print(f"[red]❌ Invalid output format: {output}[/red]")
        console.print(f"[dim]Valid options: {', '.join(valid_outputs)}[/dim]")
        raise typer.Exit(1)
    
    valid_depths = ["quick", "standard", "deep"]
    if depth not in valid_depths:
        console.print(f"[red]❌ Invalid analysis depth: {depth}[/red]")
        console.print(f"[dim]Valid options: {', '.join(valid_depths)}[/dim]")
        raise typer.Exit(1)

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
            logger.info(f"Successfully fetched repo data for {repo_url}")
        except ValueError as e:
            logger.error(f"Failed to fetch repo: {e}")
            console.print(f"[red]❌ Failed to fetch repo:[/red] {e}")
            raise typer.Exit(1)
        except Exception as e:
            logger.error(f"Unexpected error fetching repo: {e}", exc_info=True)
            console.print(f"[red]❌ Unexpected error fetching repo:[/red] {e}")
            raise typer.Exit(1)

    console.print(f"[green]✓[/green] Fetched [bold]{repo_data['full_name']}[/bold] ({repo_data['language'] or 'unknown language'})")

    # Analyze with AI
    with console.status("[cyan]Analyzing with AI (this takes ~10s)...[/cyan]"):
        try:
            summary = analyze_repo(repo_data, depth=depth)
            logger.info(f"Successfully analyzed repo {repo_data['full_name']} with depth {depth}")
        except ValueError as e:
            logger.error(f"AI analysis failed: {e}")
            console.print(f"[red]❌ AI analysis failed:[/red] {e}")
            raise typer.Exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
            console.print(f"[red]❌ Unexpected error during analysis:[/red] {e}")
            raise typer.Exit(1)

    console.print("[green]✓[/green] Analysis complete!\n")

    # Render output
    try:
        rendered = render_summary(summary, repo_data, fmt=output)
    except Exception as e:
        console.print(f"[red]❌ Failed to render output:[/red] {e}")
        raise typer.Exit(1)

    if save:
        try:
            with open(save, "w", encoding='utf-8') as f:
                f.write(rendered if output == "markdown" else _strip_ansi(rendered))
            console.print(f"\n[green]✓[/green] Saved to [bold]{save}[/bold]")
        except IOError as e:
            console.print(f"[red]❌ Failed to save file:[/red] {e}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]❌ Unexpected error saving file:[/red] {e}")
            raise typer.Exit(1)
    else:
        console.print(rendered)


def _strip_ansi(text: str) -> str:
    import re
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def main():
    app()


if __name__ == "__main__":
    main()
