"""Analyze agent tool-call JSONL for defensive anomalies."""

from __future__ import annotations

from pathlib import Path

from callstorm.detect import (
    detect_bursts,
    detect_empty_spam,
    detect_failure_thrash,
    detect_ping_pong,
    detect_retry_storms,
)
from callstorm.models import Finding, Report
from callstorm.parse import load_calls

_SEVERITY_WEIGHT = {"low": 0.5, "medium": 1.5, "high": 3.0}


def analyze(
    path: Path,
    *,
    min_retry: int = 4,
    min_ping_pong: int = 3,
    min_empty: int = 3,
    min_thrash: int = 3,
    burst_window: float = 5.0,
    burst_max: int = 12,
) -> Report:
    calls = load_calls(path)
    findings: list[Finding] = []
    findings.extend(detect_retry_storms(calls, min_retry))
    findings.extend(detect_ping_pong(calls, min_ping_pong))
    findings.extend(detect_empty_spam(calls, min_empty))
    findings.extend(detect_failure_thrash(calls, min_thrash))
    findings.extend(detect_bursts(calls, burst_window, burst_max))

    by_kind: dict[str, int] = {}
    score = 0.0
    for f in findings:
        by_kind[f.kind] = by_kind.get(f.kind, 0) + 1
        score += _SEVERITY_WEIGHT.get(f.severity, 1.0)

    denom = max(1.0, len(calls) / 20.0)
    score = score / denom

    findings.sort(key=lambda f: (-_SEVERITY_WEIGHT.get(f.severity, 0), f.start))
    return Report(
        path=str(path),
        calls=len(calls),
        findings=findings,
        score=score,
        by_kind=by_kind,
    )


def format_text(report: Report) -> str:
    lines = [
        f"callstorm: {report.path}",
        f"  calls: {report.calls}",
        f"  score: {report.score:.3f}",
        f"  findings: {len(report.findings)}",
    ]
    if report.by_kind:
        kinds = ", ".join(f"{k}={v}" for k, v in sorted(report.by_kind.items()))
        lines.append(f"  by_kind: {kinds}")
    if not report.findings:
        lines.append("  (clean - no anomalies)")
        return "\n".join(lines)
    lines.append("")
    for f in report.findings:
        lines.append(
            f"  [{f.severity}] {f.kind} @{f.start}-{f.end} {f.tool}: {f.detail}"
        )
    return "\n".join(lines)
