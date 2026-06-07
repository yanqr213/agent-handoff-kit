import json

from agent_handoff_kit.parser import parse_file, parse_markdown, parse_simple_yaml


def test_parse_markdown_sections():
    packet = parse_markdown(
        """# Owner
Team A

# Summary
Implemented a useful handoff command with enough detail.

# Validation
- pytest
- CLI check

# Risks
- Regex redaction can miss secrets.

# Next Steps
- Add team-specific rules.
"""
    )

    assert packet.owner == "Team A"
    assert packet.summary.startswith("Implemented")
    assert packet.validation == ["pytest", "CLI check"]
    assert packet.risks == ["Regex redaction can miss secrets."]
    assert packet.next_steps == ["Add team-specific rules."]


def test_parse_json_file(tmp_path):
    path = tmp_path / "handoff.json"
    path.write_text(
        json.dumps(
            {
                "owner": "Team A",
                "summary": "A detailed summary for the handoff packet.",
                "validation": ["pytest"],
                "risks": ["One known risk."],
                "next_steps": ["Review."],
            }
        ),
        encoding="utf-8",
    )

    packet = parse_file(path)
    assert packet.owner == "Team A"
    assert packet.validation == ["pytest"]


def test_parse_simple_yaml():
    data = parse_simple_yaml(
        """owner: Team A
summary: A detailed summary for the handoff packet.
validation:
  - pytest
risks:
  - One known risk.
next_steps:
  - Review.
"""
    )

    assert data["owner"] == "Team A"
    assert data["validation"] == ["pytest"]


def test_parse_simple_yaml_scalars():
    data = parse_simple_yaml(
        """require_git_diff: false
min_summary_chars: 30
fail_on_sensitive_findings: true
"""
    )

    assert data["require_git_diff"] is False
    assert data["min_summary_chars"] == 30
    assert data["fail_on_sensitive_findings"] is True
