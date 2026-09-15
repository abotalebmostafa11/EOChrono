import csv
import json
from pathlib import Path

FIELDS = ["id", "name", "date", "cloud", "size", "provider", "platform", "status", "local_path", "score", "coverage", "asset", "url"]


def write_inventory(path, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in FIELDS} for row in rows)


def write_metadata(path, row):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(row, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
