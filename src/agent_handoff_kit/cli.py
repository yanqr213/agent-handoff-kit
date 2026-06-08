"""Command line interface for Agent Handoff Kit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__
from .models import Finding, HandoffPacket, Report
from .parser import ParseError, parse_file
from .redaction import redact_packet, scan_text
from .reports import render_json, render_markdown, render_prompt
from .rules import evaluate_rules, load_rule_config, passes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-handoff-kit",
        description="Create reviewable AI coding agent handoff packets from Markdown/JSON/YAML inputs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("input", help="Path to a Markdown, JSON, or YAML handoff input file.")
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "prompt"],
        default="markdown",
        help="Report output format.",
    )
    parser.add_argument("--output", "-o", help="Write report to this path instead of stdout.")
    parser.add_argument("--config", help="Optional JSON/YAML rule configuration file.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero when quality gates fail.")
    parser.add_argument("--no-redact", action="store_true", help="Scan sensitive data but do not redact report output.")
    parser.add_argument("--diff", help="Optional file containing git diff or diff summary to include.")
    parser.add_argument("--fail-on-sensitive", action="store_true", help="Treat sensitive data findings as check failures.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        packet = parse_file(args.input)
        if args.diff:
            packet.git_diff = Path(args.diff).read_text(encoding="utf-8")

        report_packet, findings = redact_packet(packet) if not args.no_redact else (packet, scan_packet(packet))
        config = load_rule_config(args.config)
        if args.fail_on_sensitive:
            config["fail_on_sensitive_findings"] = True
        rule_results = evaluate_rules(report_packet, config=config, sensitive_count=len(findings))
        passed = passes(rule_results)
        report = Report(
            packet=report_packet,
            rule_results=rule_results,
            findings=findings,
            passed=passed,
            source=Path(args.input).as_posix(),
        )
        rendered = render_report(report, args.format)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)

        return 1 if args.check and not passed else 0
    except (OSError, ParseError, ValueError) as exc:
        sys.stderr.write(f"agent-handoff-kit: {exc}\n")
        return 2


def scan_packet(packet: HandoffPacket) -> List[Finding]:
    findings: List[Finding] = []
    fields = {
        "owner": packet.owner,
        "summary": packet.summary,
        "context": packet.context,
        "git_diff": packet.git_diff,
    }
    for field, value in fields.items():
        findings.extend(scan_text(value, field))
    for field in ("changes", "validation", "risks", "next_steps"):
        for index, value in enumerate(getattr(packet, field)):
            findings.extend(scan_text(value, f"{field}[{index}]"))
    return findings


def render_report(report: Report, output_format: str) -> str:
    if output_format == "json":
        return render_json(report)
    if output_format == "prompt":
        return render_prompt(report)
    return render_markdown(report)


if __name__ == "__main__":
    raise SystemExit(main())
