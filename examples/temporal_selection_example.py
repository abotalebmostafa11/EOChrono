#!/usr/bin/env python3
"""Reproduce the deterministic EOChrono scene-selection example."""

from __future__ import annotations

import csv
import importlib.util
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUALITY_PATH = ROOT / "EOChrono" / "core" / "quality.py"
DATA_PATH = Path(__file__).with_name("example_scenes.csv")
EXPECTED_PATH = Path(__file__).with_name("expected_selection_results.json")


def load_quality_module():
    spec = importlib.util.spec_from_file_location("eochrono_quality", QUALITY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {QUALITY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_rows():
    with DATA_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def summarize(rows):
    clouds = [float(r["cloud"]) for r in rows]
    dates = [date.fromisoformat(r["date"][:10]) for r in rows]
    months = {r["date"][:7] for r in rows}
    return {
        "selected": [r["id"] for r in rows],
        "mean_cloud": round(sum(clouds) / len(clouds), 2),
        "span_days": (max(dates) - min(dates)).days,
        "months_covered": len(months),
    }


def main():
    quality = load_quality_module()
    rows = load_rows()

    top_indices = quality.select_best(rows, count=3, mode="balanced")
    top_rows = [rows[i] for i in top_indices]
    temporal_rows = quality.balanced_time_series(rows, count=3, mode="balanced")
    monthly_rows = quality.monthly_best(rows, mode="balanced")

    actual = {
        "top_count": summarize(top_rows),
        "temporal": summarize(temporal_rows),
        "monthly": summarize(monthly_rows),
    }

    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))

    print("EOChrono 7.0.0 reproducibility example")
    print("=" * 43)
    for method in ("top_count", "temporal", "monthly"):
        r = actual[method]
        print(
            f"{method:10s} "
            f"selected={','.join(r['selected'])} "
            f"mean_cloud={r['mean_cloud']:.2f}% "
            f"span={r['span_days']} days "
            f"months={r['months_covered']}"
        )

    if actual != expected:
        print("\nResult does not match expected_selection_results.json")
        print(json.dumps(actual, indent=2))
        raise SystemExit(1)

    results_dir = Path(__file__).with_name("results")
    results_dir.mkdir(exist_ok=True)
    result_path = results_dir / "selection_results.json"
    result_path.write_text(json.dumps(actual, indent=2), encoding="utf-8")
    print(f"\nVerified successfully. Results written to {result_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
