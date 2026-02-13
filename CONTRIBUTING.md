# Contributing to Voyage GEO

Thanks for your interest in contributing! Here's how to get started.

## Setup

```bash
git clone https://github.com/Onvoyage-AI/voyage-geo-agent.git
cd voyage-geo-agent
pip install -e ".[dev]"
```

## Development Workflow

1. Create a branch from `main`
2. Make your changes
3. Run checks:
   ```bash
   python3 -m pytest tests/ -v
   python3 -m ruff check src/ tests/
   python3 -m mypy src/voyage_geo/ --ignore-missing-imports
   ```
4. Open a pull request

## Code Style

- Python 3.11+, async/await throughout
- Pydantic v2 for all data models
- Rich for CLI output
- `ruff` for linting and formatting
- Keep functions focused and files under ~300 lines

## What to Contribute

- **New AI providers** — see [docs/providers.md](./docs/providers.md)
- **New analyzers** — see [docs/analyzers.md](./docs/analyzers.md)
- **New query strategies** — see [docs/query-strategies.md](./docs/query-strategies.md)
- **Bug fixes** — check [Issues](https://github.com/Onvoyage-AI/voyage-geo-agent/issues)
- **Report improvements** — better charts, new export formats

## Reporting Bugs

Open an issue with:
- What you expected vs what happened
- Steps to reproduce
- Python version and OS
- Relevant error output

## Pull Requests

- Keep PRs focused on a single change
- Include tests for new functionality
- Update docs if you're changing interfaces
- Make sure all checks pass before requesting review
