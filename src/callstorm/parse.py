"""Parse agent tool-call JSONL into Call records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from callstorm.models import Call

TOOL_KEYS = ("tool", "name", "tool_name", "function", "fn")
ARGS_KEYS = ("arguments", "args", "input", "params", "parameters")
TS_KEYS = ("timestamp", "ts", "time", "created_at", "at")
ERR_KEYS = ("error", "ok", "success", "status", "result")


def _stable_hash(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _pick(d: dict[str, Any], keys: Iterable[str]) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _normalize_record(obj: Any, index: int) -> Call | None:
    """Accept common agent JSONL shapes."""
    if not isinstance(obj, dict):
        return None

    if "tool_call" in obj and isinstance(obj["tool_call"], dict):
        obj = {**obj, **obj["tool_call"]}
    if "function" in obj and isinstance(obj["function"], dict):
        fn = obj["function"]
        merged = dict(obj)
        merged.setdefault("name", fn.get("name"))
        if "arguments" in fn:
            merged.setdefault("arguments", fn["arguments"])
        obj = merged

    tool = _pick(obj, TOOL_KEYS)
    if not tool or not isinstance(tool, str):
        return None
    tool = tool.strip()
    if not tool:
        return None

    args = _pick(obj, ARGS_KEYS)
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            pass
    if args is None:
        args = {}
    args_empty = args in ({}, [], None, "")

    ts_raw = _pick(obj, TS_KEYS)
    timestamp: float | None = None
    if isinstance(ts_raw, (int, float)):
        timestamp = float(ts_raw)
    elif isinstance(ts_raw, str):
        try:
            timestamp = float(ts_raw)
        except ValueError:
            try:
                timestamp = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            except ValueError:
                timestamp = None

    failed = False
    err = _pick(obj, ERR_KEYS)
    if isinstance(err, bool):
        failed = err is False if "ok" in obj or "success" in obj else bool(err)
    elif isinstance(err, str):
        failed = err.lower() in ("error", "fail", "failed", "failure") or bool(err.strip())
    elif err is not None and "error" in obj:
        failed = True

    return Call(
        index=index,
        tool=tool,
        args_hash=_stable_hash(args),
        args_empty=bool(args_empty),
        timestamp=timestamp,
        failed=failed,
        raw=obj,
    )


def load_calls(path: Path) -> list[Call]:
    text = path.read_text(encoding="utf-8")
    calls: list[Call] = []
    stripped = text.strip()
    if stripped.startswith("["):
        data = json.loads(stripped)
        if not isinstance(data, list):
            raise ValueError("JSON root must be an array of call objects")
        for i, item in enumerate(data):
            c = _normalize_record(item, i)
            if c:
                calls.append(c)
        return calls

    for i, line in enumerate(text.splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {i + 1}: {exc}") from exc
        if isinstance(obj, dict) and isinstance(obj.get("tool_calls"), list):
            for tc in obj["tool_calls"]:
                c = _normalize_record(tc if isinstance(tc, dict) else {}, len(calls))
                if c:
                    calls.append(c)
            continue
        c = _normalize_record(obj, len(calls))
        if c:
            calls.append(c)
    return calls
