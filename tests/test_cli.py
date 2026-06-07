import json

from agent_handoff_kit.cli import main


def write_complete(path):
    path.write_text(
        json.dumps(
            {
                "owner": "Team A",
                "summary": "A detailed summary that should pass all default quality gates.",
                "validation": ["pytest"],
                "risks": ["Pattern-based redaction is best effort."],
                "next_steps": ["Review before sharing."],
            }
        ),
        encoding="utf-8",
    )


def test_cli_check_passes(tmp_path, capsys):
    path = tmp_path / "handoff.json"
    write_complete(path)

    code = main([str(path), "--check", "--format", "json"])
    out = capsys.readouterr().out

    assert code == 0
    assert json.loads(out)["passed"] is True


def test_cli_check_fails_for_missing_fields(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"summary": "Missing important sections."}), encoding="utf-8")

    code = main([str(path), "--check", "--format", "json"])
    out = capsys.readouterr().out

    assert code == 1
    assert json.loads(out)["passed"] is False


def test_cli_parse_error_returns_two(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")

    code = main([str(path), "--check"])
    err = capsys.readouterr().err

    assert code == 2
    assert "agent-handoff-kit:" in err


def test_cli_writes_output_file(tmp_path):
    path = tmp_path / "handoff.json"
    output = tmp_path / "reports" / "report.md"
    write_complete(path)

    code = main([str(path), "--output", str(output)])

    assert code == 0
    assert output.read_text(encoding="utf-8").startswith("# Agent Handoff Packet")
