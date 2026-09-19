from pathlib import Path

from callstorm.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_cli_clean_exit_0():
    assert main([str(EXAMPLES / "clean.jsonl")]) == 0


def test_cli_fail_on_retry():
    code = main([str(EXAMPLES / "stormy.jsonl"), "--fail-on", "retry_storm"])
    assert code == 3


def test_cli_max_score():
    code = main([str(EXAMPLES / "stormy.jsonl"), "--max-score", "0.01"])
    assert code == 2


def test_cli_json():
    assert main([str(EXAMPLES / "clean.jsonl"), "--format", "json"]) == 0


def test_cli_missing_file():
    assert main(["/no/such/file.jsonl"]) == 1
