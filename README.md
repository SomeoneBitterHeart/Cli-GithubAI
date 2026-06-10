# 🔍 RepoWise

**Understand any GitHub repo in seconds — powered by AI.**

> Paste a GitHub URL. Get a full structured breakdown: what it does, tech stack, how to install, key files, architecture, and where to start contributing.

```bash
repowise https://github.com/fastapi/fastapi
```

![RepoWise Demo](https://via.placeholder.com/800x400/0d1117/58a6ff?text=RepoWise+Demo+Screenshot)

---

## ✨ Why RepoWise?

Before contributing to open source, you often spend **30+ minutes** just figuring out:
- What does this project actually do?
- How do I set it up?
- Where are the important files?
- Where should I even start?

RepoWise answers all of this in **~10 seconds**.

---

## 🚀 Quick Start

### 1. Install

```bash
pip install repowise
```

Or run directly from source:

```bash
git clone https://github.com/YOUR_USERNAME/repowise
cd repowise
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
# Get one free at: https://console.anthropic.com
```

Or export directly:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run it

```bash
repowise https://github.com/pallets/flask
```

---

## 📖 Usage

```
Usage: repowise [OPTIONS] REPO_URL

  Analyze a GitHub repository and generate an AI-powered structured summary.

Arguments:
  REPO_URL  GitHub repo URL  [required]

Options:
  -o, --output [terminal|markdown|json]  Output format  [default: terminal]
  -d, --depth [quick|standard|deep]      Analysis depth  [default: standard]
  -s, --save TEXT                        Save output to file
  --help                                 Show this message and exit.
```

### Examples

```bash
# Standard analysis (default)
repowise https://github.com/tiangolo/fastapi

# Quick overview (faster, less detail)
repowise https://github.com/django/django --depth quick

# Deep analysis (slower, more detailed)
repowise https://github.com/pytorch/pytorch --depth deep

# Save as markdown file
repowise https://github.com/redis/redis --output markdown --save redis-summary.md

# Get raw JSON output
repowise https://github.com/golang/go --output json

# Combine options
repowise https://github.com/rust-lang/rust --depth deep --output markdown --save rust-summary.md
```

---

## 📊 What You Get

```
📦 Repository Summary ─────────────────────────────────────────
  fastapi/fastapi  ⭐⭐⭐⭐
  "FastAPI is the fastest way to build production APIs in Python"

  ★ 73,000 stars   ⑂ 6,100 forks   ⚠ 209 issues   📄 MIT

🎯 What It Does
  FastAPI is a modern, high-performance Python web framework for building
  APIs. It uses Python type hints to auto-generate OpenAPI documentation
  and provides async support out of the box...

🛠 Tech Stack
  Python  Starlette  Pydantic  Uvicorn  OpenAPI

📥 How to Install
  1. pip install fastapi
  2. pip install "uvicorn[standard]"
  3. Create a main.py and run: uvicorn main:app --reload

🚀 How to Use
  $ uvicorn main:app --reload
  # Visit http://localhost:8000/docs for auto-generated API docs

📁 Key Files
  File                  Purpose
  README.md             Full docs and examples
  fastapi/main.py       Core FastAPI class and app factory
  fastapi/routing.py    Route registration and request handling
  fastapi/params.py     Query/body/header parameter declarations
  pyproject.toml        Package metadata and dependencies

🏗 Architecture
  Starlette-based ASGI app with decorator-driven routing. Pydantic handles
  request/response validation via Python type annotations...

💡 Good First Contribution
  Look at open issues labeled "good first issue". The docs (docs/) are
  written in Markdown — fixing typos or improving examples is a great start.
```

---

## ⚙️ Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Claude API key from [console.anthropic.com](https://console.anthropic.com) |
| `GITHUB_TOKEN` | Optional | GitHub personal access token — raises rate limit from 60 to 5,000 req/hr |

---

## 🔧 Analysis Depths

| Depth | Speed | Best For |
|-------|-------|----------|
| `quick` | ~5s | Fast glance at unfamiliar repos |
| `standard` | ~10s | Default — balanced detail |
| `deep` | ~20s | Before making a PR or major contribution |

---

## 🤝 Contributing

1. Fork this repo
2. Create a branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Submit a PR!

Ideas welcome: output formats, caching, GitHub Actions integration, VS Code extension, web UI.

---

## 📄 License

MIT — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

Built with [Anthropic Claude](https://anthropic.com), [Rich](https://github.com/Textualize/rich), and [Typer](https://typer.tiangolo.com).
