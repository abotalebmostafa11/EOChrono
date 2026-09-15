import eochrono


def sample_rows():
    return [
        {"id": "S1", "name": "S1", "date": "2024-01-01", "cloud": 0, "coverage": 100},
        {"id": "S2", "name": "S2", "date": "2024-01-03", "cloud": 1, "coverage": 100},
        {"id": "S3", "name": "S3", "date": "2024-01-05", "cloud": 2, "coverage": 100},
        {"id": "S4", "name": "S4", "date": "2024-03-01", "cloud": 12, "coverage": 100},
        {"id": "S5", "name": "S5", "date": "2024-05-01", "cloud": 18, "coverage": 100},
        {"id": "S6", "name": "S6", "date": "2024-07-01", "cloud": 20, "coverage": 100},
    ]


def test_version():
    assert eochrono.__version__ == "7.0.0"


def test_selection_example():
    rows = sample_rows()
    top = [rows[index]["id"] for index in eochrono.select_best(rows, 3, "balanced")]
    temporal = [row["id"] for row in eochrono.balanced_time_series(rows, 3, "balanced")]
    monthly = [row["id"] for row in eochrono.monthly_best(rows, "balanced")]
    assert top == ["S1", "S2", "S3"]
    assert temporal == ["S1", "S4", "S5"]
    assert monthly == ["S1", "S4", "S5", "S6"]


def test_index_metadata_imports_without_qgis():
    assert "NDVI" in eochrono.INDEX_FORMULAS
