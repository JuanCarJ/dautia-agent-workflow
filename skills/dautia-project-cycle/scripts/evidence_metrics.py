#!/usr/bin/env python3
"""Summarize an evaluation corpus without treating unknowns as zero.

Input is a JSON object with a ``cases`` list. Cases may contain
``gold_profile`` (an independently reviewed label), ``recommended_profile``,
``status``, ``network_called`` and ``duration_ms``. This module measures the
corpus; it does not call Jev, change thresholds or authorize routing.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


def _read(path: str) -> dict[str, Any]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict) or not isinstance(value.get("cases"), list):
        raise ValueError("evaluation_corpus_must_have_cases")
    return value


def _known_label(value: Any) -> bool:
    """Return true only for an explicit, non-placeholder corpus label."""
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {
        "unknown", "in_progress", "pending", "none", "null",
    }


def summarize(corpus: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in corpus["cases"] if isinstance(row, dict)]
    states: dict[str, int] = {}
    for row in rows:
        state = row.get("status")
        key = state if isinstance(state, str) and state else "unknown"
        states[key] = states.get(key, 0) + 1
    labeled = [row for row in rows if _known_label(row.get("gold_profile"))]
    compared = [row for row in labeled if _known_label(row.get("recommended_profile"))]
    durations = [float(row["duration_ms"]) for row in rows
                 if isinstance(row.get("duration_ms"), (int, float))
                 and math.isfinite(float(row["duration_ms"])) and float(row["duration_ms"]) >= 0]
    sorted_durations = sorted(durations)
    p95 = sorted_durations[max(0, math.ceil(len(sorted_durations) * .95) - 1)] if sorted_durations else None
    return {
        "schema_version": 1,
        "cases": len(rows),
        "states": states,
        "network_calls": sum(row.get("network_called") is True for row in rows),
        "recommendations": sum(_known_label(row.get("recommended_profile")) for row in rows),
        "gold_labeled": len(labeled),
        "gold_compared": len(compared),
        "recommendation_precision": (sum(row.get("gold_profile") == row.get("recommended_profile") for row in compared) / len(compared)) if compared else None,
        "recommendation_coverage": (len(compared) / len(labeled)) if labeled else None,
        "unauthorized_actions": sum(row.get("authorizes_action") is True for row in rows),
        "completion_certifications": sum(row.get("certifies_completion") is True for row in rows),
        "fallback_rate": (states.get("fallback", 0) / len(rows)) if rows else None,
        "latency_ms": {
            "mean": round(statistics.mean(durations), 3) if durations else None,
            "p50": sorted_durations[len(sorted_durations) // 2] if sorted_durations else None,
            "p95": p95,
            "observed": len(durations),
        },
        "unknowns_preserved": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON corpus path or - for stdin")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(summarize(_read(args.input)), ensure_ascii=True, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
