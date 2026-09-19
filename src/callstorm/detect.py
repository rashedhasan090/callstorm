"""Detectors for storm-shaped tool-call patterns."""

from __future__ import annotations

from callstorm.models import Call, Finding


def detect_retry_storms(calls: list[Call], min_run: int) -> list[Finding]:
    findings: list[Finding] = []
    i = 0
    while i < len(calls):
        j = i + 1
        while (
            j < len(calls)
            and calls[j].tool == calls[i].tool
            and calls[j].args_hash == calls[i].args_hash
        ):
            j += 1
        run = j - i
        if run >= min_run:
            sev = "high" if run >= min_run + 2 else "medium"
            findings.append(
                Finding(
                    kind="retry_storm",
                    severity=sev,
                    start=calls[i].index,
                    end=calls[j - 1].index,
                    tool=calls[i].tool,
                    detail=f"{run} identical calls (tool={calls[i].tool}, args={calls[i].args_hash})",
                    count=run,
                )
            )
        i = j
    return findings


def detect_ping_pong(calls: list[Call], min_pairs: int) -> list[Finding]:
    findings: list[Finding] = []
    i = 0
    while i + 3 < len(calls):
        a, b = calls[i].tool, calls[i + 1].tool
        if a == b:
            i += 1
            continue
        pairs = 0
        j = i
        while j + 1 < len(calls) and calls[j].tool == a and calls[j + 1].tool == b:
            pairs += 1
            j += 2
        if pairs >= min_pairs:
            findings.append(
                Finding(
                    kind="ping_pong",
                    severity="high" if pairs >= min_pairs + 1 else "medium",
                    start=calls[i].index,
                    end=calls[j - 1].index,
                    tool=f"{a}<->{b}",
                    detail=f"{pairs} A-B pairs alternating {a!r} and {b!r}",
                    count=pairs,
                )
            )
            i = j
        else:
            i += 1
    return findings


def detect_empty_spam(calls: list[Call], min_run: int) -> list[Finding]:
    findings: list[Finding] = []
    i = 0
    while i < len(calls):
        if not calls[i].args_empty:
            i += 1
            continue
        j = i + 1
        while j < len(calls) and calls[j].args_empty and calls[j].tool == calls[i].tool:
            j += 1
        run = j - i
        if run >= min_run:
            findings.append(
                Finding(
                    kind="empty_arg_spam",
                    severity="medium" if run < min_run + 2 else "high",
                    start=calls[i].index,
                    end=calls[j - 1].index,
                    tool=calls[i].tool,
                    detail=f"{run} consecutive empty-arg calls to {calls[i].tool!r}",
                    count=run,
                )
            )
        i = j
    return findings


def detect_failure_thrash(calls: list[Call], min_run: int) -> list[Finding]:
    findings: list[Finding] = []
    i = 0
    while i < len(calls):
        if not calls[i].failed:
            i += 1
            continue
        j = i + 1
        while (
            j < len(calls)
            and calls[j].tool == calls[i].tool
            and calls[j].args_hash == calls[i].args_hash
        ):
            j += 1
        run = j - i
        failed_in_run = sum(1 for c in calls[i:j] if c.failed)
        if failed_in_run >= 1 and run >= min_run:
            findings.append(
                Finding(
                    kind="failure_thrash",
                    severity="high",
                    start=calls[i].index,
                    end=calls[j - 1].index,
                    tool=calls[i].tool,
                    detail=(
                        f"{run} identical retries with {failed_in_run} failures "
                        f"(tool={calls[i].tool})"
                    ),
                    count=run,
                )
            )
            i = j
        else:
            i += 1
    return findings


def detect_bursts(calls: list[Call], window_s: float, max_in_window: int) -> list[Finding]:
    stamped = [(c, c.timestamp) for c in calls if c.timestamp is not None]
    if len(stamped) < max_in_window:
        return []
    findings: list[Finding] = []
    left = 0
    for right in range(len(stamped)):
        while stamped[right][1] - stamped[left][1] > window_s:
            left += 1
        count = right - left + 1
        if count >= max_in_window:
            if findings and findings[-1].end >= stamped[left][0].index:
                prev = findings[-1]
                if stamped[right][0].index > prev.end:
                    findings[-1] = Finding(
                        kind="burst_rate",
                        severity="high" if count >= max_in_window + 3 else "medium",
                        start=prev.start,
                        end=stamped[right][0].index,
                        tool="*",
                        detail=f"{count} calls within {window_s:g}s (threshold {max_in_window})",
                        count=max(prev.count, count),
                    )
            else:
                findings.append(
                    Finding(
                        kind="burst_rate",
                        severity="high" if count >= max_in_window + 3 else "medium",
                        start=stamped[left][0].index,
                        end=stamped[right][0].index,
                        tool="*",
                        detail=f"{count} calls within {window_s:g}s (threshold {max_in_window})",
                        count=count,
                    )
                )
    return findings
