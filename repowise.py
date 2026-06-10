#!/usr/bin/env python3
"""
RepoWise CLI entry point.
Run with: python repowise.py <github_url>
Or after pip install: repowise <github_url>
"""
import sys
import os

# Add src to path for direct execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.main import app

if __name__ == "__main__":
    app()
