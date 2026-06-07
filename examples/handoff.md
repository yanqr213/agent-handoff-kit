# Owner
Platform Tools Team

# Summary
Implemented an offline CLI that turns AI coding agent work notes into a reviewable handoff packet.

# Context
The team needs a consistent artifact when Codex, Claude Code, Cursor, ChatGPT, or similar agents leave work for another developer.

# Changes
- Added a Python package with parser, rules, redaction, report rendering, and CLI modules.
- Added Markdown and JSON report output.
- Added tests and CI configuration.

# Validation
- Ran `pytest`.
- Ran `agent-handoff-kit examples/handoff.md --check`.

# Risks
- YAML support intentionally covers only simple top-level keys and string lists.
- Redaction uses pattern matching and cannot guarantee perfect detection.

# Next Steps
- Add organization-specific rules if stricter handoff policy is needed.
- Review generated packets before sharing outside the team.

# Git Diff
No repository diff is attached in this example.
