from agent_handoff_kit.models import HandoffPacket
from agent_handoff_kit.rules import evaluate_rules, load_rule_config, passes


def test_required_rules_fail_when_missing_fields():
    results = evaluate_rules(HandoffPacket(summary="too short"))
    codes = {result.code for result in results}

    assert "missing_owner" in codes
    assert "missing_validation" in codes
    assert "missing_risks" in codes
    assert "missing_next_steps" in codes
    assert not passes(results)


def test_rules_pass_for_complete_packet():
    packet = HandoffPacket(
        owner="Team A",
        summary="This summary contains enough detail to pass the default gate.",
        validation=["pytest"],
        risks=["No production rollout yet."],
        next_steps=["Review the generated handoff."],
    )

    assert evaluate_rules(packet) == []


def test_sensitive_findings_can_fail_gate():
    packet = HandoffPacket(
        owner="Team A",
        summary="This summary contains enough detail to pass the default gate.",
        validation=["pytest"],
        risks=["No production rollout yet."],
        next_steps=["Review the generated handoff."],
    )

    results = evaluate_rules(packet, {"fail_on_sensitive_findings": True}, sensitive_count=1)

    assert any(result.code == "sensitive_data_detected" for result in results)
    assert not passes(results)


def test_load_yaml_config_false_boolean(tmp_path):
    path = tmp_path / "rules.yaml"
    path.write_text("require_git_diff: false\nmin_summary_chars: 20\n", encoding="utf-8")

    config = load_rule_config(str(path))

    assert config["require_git_diff"] is False
