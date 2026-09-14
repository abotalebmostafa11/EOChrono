import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "EOChrono" / "core" / "inventory.py"


def load_inventory():
    spec = importlib.util.spec_from_file_location("eochrono_inventory", INVENTORY_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_round_trip_fields(tmp_path):
    inv = load_inventory()
    row = {
        "id": "S1",
        "name": "Scene 1",
        "date": "2024-01-01",
        "cloud": 0,
        "size": 123,
        "provider": "illustrative",
        "platform": "test",
        "status": "Downloaded",
        "local_path": "/tmp/S1.tif",
        "score": 100,
        "coverage": 100,
        "asset": "data",
        "url": "https://example.invalid/S1",
    }

    out = tmp_path / "inventory.csv"
    inv.write_inventory(out, [row])

    with out.open(newline="", encoding="utf-8-sig") as f:
        loaded = list(csv.DictReader(f))

    assert len(loaded) == 1
    assert list(loaded[0].keys()) == inv.FIELDS
    assert loaded[0]["id"] == "S1"
    assert loaded[0]["status"] == "Downloaded"


def test_json_metadata_preserves_record(tmp_path):
    inv = load_inventory()
    row = {"id": "S1", "date": "2024-01-01", "provider": "illustrative"}
    out = tmp_path / "S1.json"

    inv.write_metadata(out, row)

    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == row
