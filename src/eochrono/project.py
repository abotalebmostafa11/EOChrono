import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT = {
    "version": "7.0.0",
    "satellite": "Sentinel-2",
    "start": "2018-01-01",
    "end": "2025-12-31",
    "cloud": 20.0,
    "limit": 1000,
    "monthly": False,
    "ranking": "balanced",
    "best_count": 12,
    "output": "",
    "workers": 3,
    "resume": True,
    "verify": True,
}


def save_project(path, settings, rows=None):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = dict(DEFAULT)
    data.update(settings)
    data["saved_at"] = datetime.now(timezone.utc).isoformat()
    data["rows"] = rows or []
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def load_project(path):
    data = dict(DEFAULT)
    data.update(json.loads(Path(path).read_text(encoding="utf-8")))
    return data
