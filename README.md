# callstorm

**Offline CLI that hunts defensive anomalies in agent tool-call JSONL.**

Agent transcripts often hide failure modes that a sequence diagram will not flag: the same tool hammered with identical args, A↔B ping-pong loops, empty-arg spam, failure thrash, and burst-rate spikes. `callstorm` scores those patterns and exits non-zero for CI.

## Why this is novel

`toolflow` turns tool-call JSONL into Mermaid diagrams. `runseal` seals a single command run. `promptfence` lints system prompts. **callstorm** is different: it treats the *call stream itself* as a security/reliability signal and looks for storm-shaped behavior that burns tokens, masks stuck agents, and can amplify side effects.

It is **not** a fork or thin wrapper of an existing project.

Distinct from: sandclock, tokpack, hushdiff, runseal, toolflow, hedgescope, diffintent, promptfence, aegispath, rippleguard, shardroom, claimcite, citationcheckertool, stubtruth.

## Install

```bash
pip install -e .
# or
pip install -e ".[dev]"
```

Requires Python 3.10+.

## Usage

```bash
# Score a transcript
callstorm examples/stormy.jsonl

# JSON for tooling
callstorm examples/stormy.jsonl --format json

# CI gates
callstorm path/to/trace.jsonl --fail-on retry_storm --fail-on ping_pong
callstorm path/to/trace.jsonl --max-score 2.0
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | OK (or no failing gates requested) |
| 1 | Bad args / unreadable or invalid file |
| 2 | `--max-score` exceeded |
| 3 | `--fail-on KIND` matched at least one finding |

### Finding kinds

| Kind | What it catches |
|------|-----------------|
| `retry_storm` | N identical tool+args calls in a row |
| `ping_pong` | Alternating A-B-A-B tool pairs |
| `empty_arg_spam` | Consecutive empty/null argument calls |
| `failure_thrash` | Identical retries after failures |
| `burst_rate` | Too many timestamped calls in a short window |

## Demo

```bash
callstorm examples/clean.jsonl
# score 0 — clean

callstorm examples/stormy.jsonl --fail-on retry_storm
# exit 3 — retry storm + empty-arg spam + ping-pong
```

## Accepted JSONL shapes

Each line may use any of these field aliases:

- tool: `tool`, `name`, `tool_name`, `function`, `fn`
- args: `arguments`, `args`, `input`, `params`, `parameters` (stringified JSON ok)
- time: `timestamp`, `ts`, `time`, `created_at`, `at`
- status: `error`, `ok`, `success`, `status`

Also accepts OpenAI-style `tool_calls` / `function` nesting and a root JSON array.

## Limitations

- Heuristic thresholds (tunable via flags); not a behavioral ML model.
- Burst detection needs timestamps; other detectors work without them.
- Does not execute tools or talk to models — fully offline.

## License

MIT
