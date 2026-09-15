from __future__ import annotations

import csv
from importlib.resources import files

from .quality import balanced_time_series, monthly_best, select_best


def demo():
    data_path = files("eochrono.data").joinpath("example_scenes.csv")
    with data_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    top = [rows[index]["id"] for index in select_best(rows, 3, "balanced")]
    temporal = [row["id"] for row in balanced_time_series(rows, 3, "balanced")]
    monthly = [row["id"] for row in monthly_best(rows, "balanced")]
    print("EOChrono 7.0.0 deterministic example")
    print("Top-count:", ", ".join(top))
    print("Temporal:", ", ".join(temporal))
    print("Monthly:", ", ".join(monthly))
    return 0


def main():
    return demo()
