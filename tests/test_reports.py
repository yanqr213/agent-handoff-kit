import json

from agent_handoff_kit.models import Finding, HandoffPacket, Report, RuleResult
from agent_handoff_kit.reports import render_json, render_markdown, render_prompt


def make_report():
    return Report(
        packet=HandoffPacket(
            owner="Team A",
            summary="A detailed handoff summary.",
            validation=["pytest"],
            risks=["One risk."],
            next_steps=["Review."],
        ),
        rule_results=[RuleResult(code="summary_too_short", message="Too short.", severity="warning")],
        findings=[Finding(kind="email", field="summary", redacted="[REDACTED_EMAIL]")],
        passed=True,
        source="handoff.md",
    )


def test_render_markdown_contains_sections():
    markdown = render_markdown(make_report())

    assert "# Agent Handoff Packet" in markdown
    assert "## Quality Gate" in markdown
    assert "`summary_too_short`" in markdown
    assert "Sensitive Data Scan" in markdown


def test_render_json_is_machine_readable():
    data = json.loads(render_json(make_report()))

    assert data["passed"] is True
    assert data["packet"]["owner"] == "Team A"
    assert data["findings"][0]["kind"] == "email"


def test_render_prompt_is_agent_ready():
    prompt = render_prompt(make_report())

    assert "# Agent Continuation Prompt" in prompt
    assert "You are continuing work from a previous AI coding agent" in prompt
    assert "## Next Actions" in prompt
    assert "1. Review." in prompt
    assert "## Instructions For The Next Agent" in prompt
