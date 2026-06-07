"""Data models used by Agent Handoff Kit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HandoffPacket:
    """Normalized handoff data consumed by rules and renderers."""

    owner: str = ""
    summary: str = ""
    context: str = ""
    changes: List[str] = field(default_factory=list)
    validation: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    git_diff: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner": self.owner,
            "summary": self.summary,
            "context": self.context,
            "changes": list(self.changes),
            "validation": list(self.validation),
            "risks": list(self.risks),
            "next_steps": list(self.next_steps),
            "git_diff": self.git_diff,
        }


@dataclass
class RuleResult:
    """A quality rule finding."""

    code: str
    message: str
    severity: str = "error"

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message, "severity": self.severity}


@dataclass
class Finding:
    """A sensitive-data finding."""

    kind: str
    field: str
    redacted: str
    severity: str = "warning"

    def to_dict(self) -> Dict[str, str]:
        return {
            "kind": self.kind,
            "field": self.field,
            "redacted": self.redacted,
            "severity": self.severity,
        }


@dataclass
class Report:
    """Fully evaluated handoff report."""

    packet: HandoffPacket
    rule_results: List[RuleResult] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    passed: bool = True
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "source": self.source,
            "packet": self.packet.to_dict(),
            "rules": [item.to_dict() for item in self.rule_results],
            "findings": [item.to_dict() for item in self.findings],
        }
