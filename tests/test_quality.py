import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUALITY_PATH = ROOT / "EOChrono" / "core" / "quality.py"


def load_quality():
    spec = importlib.util.spec_from_file_location("eochrono_quality", QUALITY_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_rows():
    return [
        {"id": "S1", "name": "S1", "date": "2024-01-01", "cloud": 0, "coverage": 100, "provider": "illustrative"},
        {"id": "S2", "name": "S2", "date": "2024-01-03", "cloud": 1, "coverage": 100, "provider": "illustrative"},
        {"id": "S3", "name": "S3", "date": "2024-01-05", "cloud": 2, "coverage": 100, "provider": "illustrative"},
        {"id": "S4", "name": "S4", "date": "2024-03-01", "cloud": 12, "coverage": 100, "provider": "illustrative"},
        {"id": "S5", "name": "S5", "date": "2024-05-01", "cloud": 18, "coverage": 100, "provider": "illustrative"},
        {"id": "S6", "name": "S6", "date": "2024-07-01", "cloud": 20, "coverage": 100, "provider": "illustrative"},
    ]


def test_balanced_scores_match_manuscript_example():
    q = load_quality()
    scores = [round(q.score(r, "balanced"), 2) for r in sample_rows()]
    assert scores == [100.00, 99.35, 98.70, 92.20, 88.30, 87.00]


def test_selection_results_match_reproducible_example():
    q = load_quality()
    rows = sample_rows()

    top = [rows[i]["id"] for i in q.select_best(rows, 3, "balanced")]
    temporal = [r["id"] for r in q.balanced_time_series(rows, 3, "balanced")]
    monthly = [r["id"] for r in q.monthly_best(rows, "balanced")]

    assert top == ["S1", "S2", "S3"]
    assert temporal == ["S1", "S4", "S5"]
    assert monthly == ["S1", "S4", "S5", "S6"]


def test_dedupe_prefers_first_duplicate_identifier():
    q = load_quality()
    rows = [
        {"id": "A", "name": "first", "date": "2024-01-01"},
        {"id": "A", "name": "duplicate", "date": "2024-02-01"},
        {"id": "B", "name": "second", "date": "2024-03-01"},
    ]
    out = q.dedupe(rows)
    assert [r["name"] for r in out] == ["first", "second"]


def test_missing_cloud_uses_neutral_quality_value():
    q = load_quality()
    row = {"cloud": None, "coverage": 100}
    assert q.score(row, "lowest_cloud") == 50
    assert q.score(row, "balanced") == 67.5
