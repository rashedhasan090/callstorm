"""Data models for callstorm."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Call:
    index: int
    tool: str
    args_hash: str
    args_empty: bool
    timestamp: float | None
    failed: bool
    raw: dict[str, Any]


@dataclass
class Finding:
    kind: str
    severity: str  # low | medium | high
    start: int
    end: int
    tool: str
    detail: str
    count: int = 1


@dataclass
class Report:
    path: str
    calls: int
    findings: list[Finding] = field(default_factory=list)
    score: float = 0.0
    by_kind: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "calls": self.calls,
            "score": round(self.score, 3),
            "by_kind": self.by_kind,
            "findings": [asdict(f) for f in self.findings],
        }
