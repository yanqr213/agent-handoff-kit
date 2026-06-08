"""Markdown, JSON, and continuation-prompt report rendering."""

from __future__ import annotations

import json
from typing import Iterable, List

from .models import Finding, HandoffPacket, Report, RuleResult


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"


def render_markdown(report: Report) -> str:
    packet = report.packet
    lines: List[str] = [
        "# Agent Handoff Packet",
        "",
        f"Status: {'PASS' if report.passed else 'FAIL'}",
    ]
    if report.source:
        lines.extend(["", f"Source: `{report.source}`"])

    lines.extend(
        [
            "",
            "## Owner",
            packet.owner or "_Missing_",
            "",
            "## Summary",
            packet.summary or "_Missing_",
            "",
            "## Context",
            packet.context or "_Not provided_",
            "",
            "## Changes",
            render_items(packet.changes, "_No changes listed_"),
            "",
            "## Validation",
            render_items(packet.validation, "_No validation listed_"),
            "",
            "## Risks",
            render_items(packet.risks, "_No risks listed_"),
            "",
            "## Next Steps",
            render_items(packet.next_steps, "_No next steps listed_"),
        ]
    )

    if packet.git_diff:
        lines.extend(["", "## Git Diff Summary", "```diff", packet.git_diff.strip(), "```"])

    lines.extend(["", "## Quality Gate", render_rule_results(report.rule_results)])
    lines.extend(["", "## Sensitive Data Scan", render_findings(report.findings)])
    return "\n".join(lines).rstrip() + "\n"


def render_prompt(report: Report) -> str:
    packet = report.packet
    status = "PASS" if report.passed else "FAIL"
    lines: List[str] = [
        "# Agent Continuation Prompt",
        "",
        "You are continuing work from a previous AI coding agent. Treat this handoff as context, then verify the current repository state before making changes.",
        "",
        f"Gate status: {status}",
    ]
    if report.source:
        lines.append(f"Source: `{report.source}`")
    lines.extend(
        [
            "",
            "## Objective",
            packet.summary or "_No objective summary provided._",
            "",
            "## Owner",
            packet.owner or "_Missing_",
            "",
            "## Context",
            packet.context or "_No context provided._",
            "",
            "## Completed Changes",
            render_items(packet.changes, "_No completed changes listed._"),
            "",
            "## Validation Already Run",
            render_items(packet.validation, "_No validation listed._"),
            "",
            "## Known Risks",
            render_items(packet.risks, "_No risks listed._"),
            "",
            "## Next Actions",
            render_numbered_items(packet.next_steps, "_No next actions listed._"),
        ]
    )

    if packet.git_diff:
        lines.extend(["", "## Diff Or Change Summary", "```diff", packet.git_diff.strip(), "```"])

    lines.extend(["", "## Quality Gate Findings", render_rule_results(report.rule_results)])
    lines.extend(["", "## Sensitive Data Findings", render_findings(report.findings)])
    lines.extend(
        [
            "",
            "## Instructions For The Next Agent",
            "- Confirm the worktree status and read the relevant files before editing.",
            "- Preserve user changes that are not part of your task.",
            "- Start with the highest-risk unresolved next action, then rerun the listed validation commands.",
            "- Update this handoff packet when you finish so the next person or agent can continue cleanly.",
        ]
    )
    if not report.passed:
        lines.extend(
            [
                "",
                "## Before Continuing",
                "Resolve the quality gate findings above or explicitly document why they are acceptable for this handoff.",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_items(items: Iterable[str], empty: str) -> str:
    values = [item.strip() for item in items if item.strip()]
    if not values:
        return empty
    return "\n".join(f"- {item}" for item in values)


def render_numbered_items(items: Iterable[str], empty: str) -> str:
    values = [item.strip() for item in items if item.strip()]
    if not values:
        return empty
    return "\n".join(f"{index}. {item}" for index, item in enumerate(values, start=1))


def render_rule_results(results: List[RuleResult]) -> str:
    if not results:
        return "- PASS: no quality issues found"
    return "\n".join(f"- {result.severity.upper()} `{result.code}`: {result.message}" for result in results)


def render_findings(findings: List[Finding]) -> str:
    if not findings:
        return "- PASS: no sensitive data patterns found"
    return "\n".join(
        f"- {finding.severity.upper()} `{finding.kind}` in `{finding.field}` -> {finding.redacted}"
        for finding in findings
    )
