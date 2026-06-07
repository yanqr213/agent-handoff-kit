"""Secret and PII scanning plus redaction."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Callable, Iterable, List, Tuple

from .models import Finding, HandoffPacket


Pattern = Tuple[str, re.Pattern[str], str | Callable[[re.Match[str]], str]]


PATTERNS: List[Pattern] = [
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[REDACTED_EMAIL]"),
    ("phone", re.compile(r"\b(?:\+?\d[\d .()/-]{7,}\d)\b"), "[REDACTED_PHONE]"),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "[REDACTED_OPENAI_KEY]"),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (
        "generic_secret",
        re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*([^\s`'\";,]{8,})"),
        lambda match: f"{match.group(1)}=[REDACTED_SECRET]",
    ),
]


def scan_text(text: str, field: str) -> List[Finding]:
    findings: List[Finding] = []
    for kind, pattern, replacement in PATTERNS:
        for match in pattern.finditer(text):
            redacted = replacement(match) if callable(replacement) else replacement
            findings.append(Finding(kind=kind, field=field, redacted=redacted))
    return findings


def redact_text(text: str) -> str:
    redacted = text
    for _, pattern, replacement in PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_packet(packet: HandoffPacket) -> tuple[HandoffPacket, List[Finding]]:
    findings: List[Finding] = []

    def redact_field(value: str, field: str) -> str:
        findings.extend(scan_text(value, field))
        return redact_text(value)

    def redact_list(values: Iterable[str], field: str) -> List[str]:
        result: List[str] = []
        for index, item in enumerate(values):
            result.append(redact_field(item, f"{field}[{index}]"))
        return result

    redacted = replace(
        packet,
        owner=redact_field(packet.owner, "owner"),
        summary=redact_field(packet.summary, "summary"),
        context=redact_field(packet.context, "context"),
        changes=redact_list(packet.changes, "changes"),
        validation=redact_list(packet.validation, "validation"),
        risks=redact_list(packet.risks, "risks"),
        next_steps=redact_list(packet.next_steps, "next_steps"),
        git_diff=redact_field(packet.git_diff, "git_diff"),
    )
    return redacted, findings
