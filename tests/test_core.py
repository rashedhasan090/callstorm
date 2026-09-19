from pathlib import Path

from callstorm.core import analyze, load_calls

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_load_stormy_count():
    calls = load_calls(EXAMPLES / "stormy.jsonl")
    assert len(calls) == 16


def test_stormy_findings():
    report = analyze(EXAMPLES / "stormy.jsonl", min_retry=4, min_ping_pong=3, min_empty=3)
    kinds = {f.kind for f in report.findings}
    assert "retry_storm" in kinds
    assert "empty_arg_spam" in kinds
    assert "ping_pong" in kinds
    assert report.score > 0


def test_clean_is_clean():
    report = analyze(EXAMPLES / "clean.jsonl")
    assert report.findings == []
    assert report.score == 0.0


def test_openai_nested_shape(tmp_path: Path):
    p = tmp_path / "nested.jsonl"
    p.write_text(
        '{"tool_calls":[{"function":{"name":"search","arguments":"{\\"q\\":\\"x\\"}"}}]}\n'
        '{"tool_calls":[{"function":{"name":"search","arguments":"{\\"q\\":\\"x\\"}"}}]}\n'
        '{"tool_calls":[{"function":{"name":"search","arguments":"{\\"q\\":\\"x\\"}"}}]}\n'
        '{"tool_calls":[{"function":{"name":"search","arguments":"{\\"q\\":\\"x\\"}"}}]}\n',
        encoding="utf-8",
    )
    report = analyze(p, min_retry=4)
    assert any(f.kind == "retry_storm" for f in report.findings)
