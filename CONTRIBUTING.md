# Contributing

Thanks for helping improve Agent Handoff Kit.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
pytest
```

## Project Principles

- Keep the CLI offline by default.
- Prefer the Python standard library unless a dependency provides clear value.
- Treat redaction as a safety net, not a guarantee.
- Keep handoff reports deterministic and easy to review in code review.
- Add focused tests for parser, rules, redaction, rendering, and CLI behavior.

## Pull Request Checklist

- Tests pass with `pytest`.
- README and examples are updated when behavior changes.
- New quality rules include documentation and tests.
- No real secrets, tokens, or private data are committed.
