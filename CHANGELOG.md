# Changelog

All notable changes to this project will be documented in this file.

## 0.2.0 - 2026-06-08

- Added `--format prompt` to generate agent-ready continuation prompts for Codex, Claude Code, Cursor, and similar tools.
- Added report rendering tests and CLI coverage for continuation prompt output.
- Added CI smoke coverage for prompt rendering.
- Added package URL metadata.
- Expanded Chinese and English README documentation for agent continuation workflows.

## 0.1.0 - 2026-06-08

- Initial local release.
- Added Markdown, JSON, and simple YAML handoff input parsing.
- Added quality gates for owner, summary, validation, risks, next steps, and optional git diff.
- Added secret and PII scanning with report redaction.
- Added Markdown and JSON report rendering.
- Added `--check` CLI mode for CI and local enforcement.
