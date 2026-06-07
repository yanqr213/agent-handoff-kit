"""Input parsing for Markdown, JSON, and a small YAML subset."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .models import HandoffPacket


SECTION_ALIASES = {
    "owner": "owner",
    "负责人": "owner",
    "summary": "summary",
    "摘要": "summary",
    "context": "context",
    "背景": "context",
    "changes": "changes",
    "change summary": "changes",
    "变更": "changes",
    "validation": "validation",
    "验证": "validation",
    "risks": "risks",
    "risk": "risks",
    "风险": "risks",
    "next steps": "next_steps",
    "next_steps": "next_steps",
    "todo": "next_steps",
    "未完成事项": "next_steps",
    "后续": "next_steps",
    "git diff": "git_diff",
    "diff": "git_diff",
}

LIST_FIELDS = {"changes", "validation", "risks", "next_steps"}


class ParseError(ValueError):
    """Raised when handoff input cannot be parsed."""


def parse_file(path: str | Path) -> HandoffPacket:
    input_path = Path(path)
    text = input_path.read_text(encoding="utf-8")
    suffix = input_path.suffix.lower()
    if suffix == ".json":
        return packet_from_mapping(json.loads(text))
    if suffix in {".yaml", ".yml"}:
        return packet_from_mapping(parse_simple_yaml(text))
    return parse_markdown(text)


def parse_markdown(text: str) -> HandoffPacket:
    sections = split_markdown_sections(text)
    normalized: Dict[str, Any] = {}

    for title, body in sections:
        key = SECTION_ALIASES.get(normalize_heading(title))
        if not key:
            continue
        if key in LIST_FIELDS:
            normalized[key] = parse_markdown_list(body)
        elif key == "git_diff":
            normalized[key] = body.strip()
        else:
            normalized[key] = clean_scalar(body)

    if not normalized and text.strip():
        normalized["summary"] = text.strip()

    return packet_from_mapping(normalized)


def split_markdown_sections(text: str) -> List[Tuple[str, str]]:
    lines = text.splitlines()
    sections: List[Tuple[str, List[str]]] = []
    current_title = ""
    current_body: List[str] = []

    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            if current_title or current_body:
                sections.append((current_title, current_body))
            current_title = match.group(2).strip()
            current_body = []
        else:
            current_body.append(line)

    if current_title or current_body:
        sections.append((current_title, current_body))

    if sections and sections[0][0] == "":
        sections = sections[1:]
    return [(title, "\n".join(body).strip()) for title, body in sections]


def parse_markdown_list(body: str) -> List[str]:
    items: List[str] = []
    current: List[str] = []

    for line in body.splitlines():
        match = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$", line)
        if match:
            if current:
                items.append(clean_scalar("\n".join(current)))
            current = [match.group(1).strip()]
        elif current and line.strip():
            current.append(line.strip())
        elif line.strip():
            items.append(clean_scalar(line))

    if current:
        items.append(clean_scalar("\n".join(current)))

    return [item for item in items if item]


def packet_from_mapping(data: Dict[str, Any]) -> HandoffPacket:
    if not isinstance(data, dict):
        raise ParseError("handoff input must be an object or sectioned Markdown")

    normalized: Dict[str, Any] = {}
    for key, value in data.items():
        field = SECTION_ALIASES.get(normalize_heading(str(key)), normalize_heading(str(key)))
        if field in {"nextsteps", "next-steps"}:
            field = "next_steps"
        if field not in {"owner", "summary", "context", "changes", "validation", "risks", "next_steps", "git_diff"}:
            continue
        normalized[field] = value

    return HandoffPacket(
        owner=as_string(normalized.get("owner")),
        summary=as_string(normalized.get("summary")),
        context=as_string(normalized.get("context")),
        changes=as_list(normalized.get("changes")),
        validation=as_list(normalized.get("validation")),
        risks=as_list(normalized.get("risks")),
        next_steps=as_list(normalized.get("next_steps")),
        git_diff=as_string(normalized.get("git_diff")),
        raw=dict(data),
    )


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Parse a conservative YAML subset: top-level scalars and string lists."""

    result: Dict[str, Any] = {}
    current_key = ""

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith((" ", "\t")):
            if current_key and raw_line.strip().startswith("- "):
                result.setdefault(current_key, []).append(parse_yaml_scalar(raw_line.strip()[2:].strip()))
                continue
            raise ParseError("only top-level keys and simple lists are supported for YAML")
        if ":" not in raw_line:
            raise ParseError("invalid YAML line; expected key: value")
        key, value = raw_line.split(":", 1)
        current_key = key.strip()
        value = value.strip()
        if value == "":
            result[current_key] = []
        else:
            result[current_key] = parse_yaml_scalar(value)

    return result


def normalize_heading(value: str) -> str:
    return re.sub(r"[\s_]+", " ", value.strip().strip(":").lower())


def clean_scalar(value: Any) -> str:
    return as_string(value).strip()


def as_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return "\n".join(str(item) for item in value)
    return str(value)


def as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_scalar(item) for item in value if clean_scalar(item)]
    if isinstance(value, tuple):
        return [clean_scalar(item) for item in value if clean_scalar(item)]
    text = clean_scalar(value)
    if not text:
        return []
    if "\n" in text:
        return [item for item in parse_markdown_list(text) if item]
    return [text]


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_yaml_scalar(value: str) -> Any:
    unquoted = unquote(value)
    lowered = unquoted.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    try:
        return int(unquoted)
    except ValueError:
        return unquoted


def load_many(paths: Iterable[str | Path]) -> List[HandoffPacket]:
    return [parse_file(path) for path in paths]
