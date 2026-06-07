"""Quality gate rules for handoff packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .models import HandoffPacket, RuleResult
from .parser import parse_simple_yaml


DEFAULT_CONFIG: Dict[str, Any] = {
    "required_fields": ["owner", "summary", "validation", "risks", "next_steps"],
    "min_summary_chars": 20,
    "min_validation_items": 1,
    "min_risk_items": 1,
    "min_next_step_items": 1,
    "require_git_diff": False,
    "fail_on_sensitive_findings": False,
}


def load_rule_config(path: str | None) -> Dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if not path:
        return config
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        loaded = json.loads(text)
    else:
        loaded = parse_simple_yaml(text)
    if not isinstance(loaded, dict):
        raise ValueError("rule config must be an object")
    config.update(loaded)
    return config


def evaluate_rules(packet: HandoffPacket, config: Dict[str, Any] | None = None, sensitive_count: int = 0) -> List[RuleResult]:
    cfg = dict(DEFAULT_CONFIG)
    if config:
        cfg.update(config)

    results: List[RuleResult] = []
    required = set(cfg.get("required_fields", []))

    for field in sorted(required):
        value = getattr(packet, field, None)
        if isinstance(value, list):
            missing = len(value) == 0
        else:
            missing = not str(value or "").strip()
        if missing:
            results.append(RuleResult(code=f"missing_{field}", message=f"Required field '{field}' is missing."))

    min_summary = int(cfg.get("min_summary_chars", 0) or 0)
    if packet.summary and len(packet.summary.strip()) < min_summary:
        results.append(
            RuleResult(
                code="summary_too_short",
                message=f"Summary should be at least {min_summary} characters.",
                severity="warning",
            )
        )

    minimums = {
        "validation": int(cfg.get("min_validation_items", 0) or 0),
        "risks": int(cfg.get("min_risk_items", 0) or 0),
        "next_steps": int(cfg.get("min_next_step_items", 0) or 0),
    }
    for field, minimum in minimums.items():
        value = getattr(packet, field)
        if len(value) < minimum:
            results.append(
                RuleResult(
                    code=f"too_few_{field}",
                    message=f"Field '{field}' should contain at least {minimum} item(s).",
                )
            )

    if bool(cfg.get("require_git_diff")) and not packet.git_diff.strip():
        results.append(RuleResult(code="missing_git_diff", message="Git diff summary is required."))

    if bool(cfg.get("fail_on_sensitive_findings")) and sensitive_count:
        results.append(
            RuleResult(
                code="sensitive_data_detected",
                message=f"{sensitive_count} sensitive data finding(s) detected.",
            )
        )

    return results


def passes(results: List[RuleResult]) -> bool:
    return not any(result.severity == "error" for result in results)
