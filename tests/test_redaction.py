from agent_handoff_kit.models import HandoffPacket
from agent_handoff_kit.redaction import redact_packet, redact_text, scan_text


def test_redacts_email_and_openai_key():
    text = "Contact dev@team.test with sk-testsecretkeyvalue1234567890"

    redacted = redact_text(text)

    assert "dev@team.test" not in redacted
    assert "sk-testsecretkeyvalue1234567890" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_OPENAI_KEY]" in redacted


def test_scan_reports_field():
    findings = scan_text("token=abcdefghi123456", "summary")

    assert findings[0].kind == "generic_secret"
    assert findings[0].field == "summary"


def test_redact_packet_lists():
    packet = HandoffPacket(
        owner="Team A",
        summary="A detailed summary with dev@team.test inside.",
        validation=["pytest token=abcdefghi123456"],
        risks=["None"],
        next_steps=["Review"],
    )

    redacted, findings = redact_packet(packet)

    assert "[REDACTED_EMAIL]" in redacted.summary
    assert "token=[REDACTED_SECRET]" in redacted.validation[0]
    assert len(findings) == 2
