"""CLI entrypoint for callstorm."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from callstorm import __version__
from callstorm.core import analyze, format_text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="callstorm",
        description=(
            "Detect retry storms, ping-pong loops, empty-arg spam, "
            "failure thrash, and burst-rate spikes in agent tool-call JSONL."
        ),
    )
    p.add_argument("path", type=Path, help="Path to a .jsonl (or JSON array) transcript")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--min-retry", type=int, default=4, help="Identical-call run length (default 4)")
    p.add_argument("--min-ping-pong", type=int, default=3, help="A-B pair count (default 3)")
    p.add_argument("--min-empty", type=int, default=3, help="Empty-arg run length (default 3)")
    p.add_argument("--min-thrash", type=int, default=3, help="Failure-thrash run length (default 3)")
    p.add_argument("--burst-window", type=float, default=5.0, help="Burst window seconds (default 5)")
    p.add_argument("--burst-max", type=int, default=12, help="Max calls in burst window (default 12)")
    p.add_argument(
        "--max-score",
        type=float,
        default=None,
        help="Exit 2 if normalized score exceeds this threshold",
    )
    p.add_argument(
        "--fail-on",
        action="append",
        default=[],
        metavar="KIND",
        help=(
            "Exit 3 if any finding of KIND exists "
            "(retry_storm|ping_pong|empty_arg_spam|failure_thrash|burst_rate). Repeatable."
        ),
    )
    p.add_argument("--version", action="version", version=f"callstorm {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path: Path = args.path
    if not path.is_file():
        print(f"callstorm: not a file: {path}", file=sys.stderr)
        return 1
    try:
        report = analyze(
            path,
            min_retry=args.min_retry,
            min_ping_pong=args.min_ping_pong,
            min_empty=args.min_empty,
            min_thrash=args.min_thrash,
            burst_window=args.burst_window,
            burst_max=args.burst_max,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"callstorm: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_text(report))

    if args.max_score is not None and report.score > args.max_score:
        return 2
    fail_kinds = set(args.fail_on)
    if fail_kinds and any(f.kind in fail_kinds for f in report.findings):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
