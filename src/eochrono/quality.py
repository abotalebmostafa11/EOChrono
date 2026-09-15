from collections import Counter
from datetime import datetime


def cloud(record):
    try:
        return max(0, min(100, float(record.get("cloud"))))
    except (TypeError, ValueError):
        return None


def coverage(record):
    try:
        return max(0, min(100, float(record.get("coverage"))))
    except (TypeError, ValueError):
        return None


def score(record, mode="balanced"):
    c = cloud(record)
    cov = coverage(record)
    if mode == "lowest_cloud":
        return 50 if c is None else 100 - c
    if mode == "coverage":
        return cov
    return ((50 if c is None else 100 - c) * 0.65) + cov * 0.35


def dedupe(rows):
    seen = set()
    out = []
    for record in rows:
        key = record.get("id") or (record.get("name"), record.get("date"))
        if key in seen:
            continue
        seen.add(key)
        out.append(record)
    return out


def select_best(rows, count=12, mode="balanced"):
    return sorted(
        range(len(rows)),
        key=lambda index: score(rows[index], mode),
        reverse=True,
    )[: min(count, len(rows))]


def monthly_best(rows, mode="balanced"):
    groups = {}
    for record in rows:
        groups.setdefault(str(record.get("date") or "")[:7], []).append(record)
    out = []
    for key in sorted(groups):
        indices = select_best(groups[key], 1, mode)
        out.extend(groups[key][index] for index in indices)
    return out


def balanced_time_series(rows, count, mode="balanced"):
    if not rows:
        return []
    rows = sorted(rows, key=lambda record: str(record.get("date") or ""))
    selected = []
    remaining = list(range(len(rows)))
    while remaining and len(selected) < min(count, len(rows)):
        best = None
        best_value = -1e9
        for index in remaining:
            date_text = str(rows[index].get("date") or "")[:10]
            try:
                current_date = datetime.fromisoformat(date_text)
            except ValueError:
                current_date = None
            quality = score(rows[index], mode)
            spacing = 100
            if current_date and selected:
                distances = []
                for selected_index in selected:
                    try:
                        selected_date = datetime.fromisoformat(str(rows[selected_index].get("date"))[:10])
                        distances.append(abs((current_date - selected_date).days))
                    except (TypeError, ValueError):
                        pass
                if distances:
                    spacing = min(distances)
            value = quality + min(spacing, 120) * 0.35
            if value > best_value:
                best_value = value
                best = index
        selected.append(best)
        remaining.remove(best)
    return [rows[index] for index in sorted(selected, key=lambda i: str(rows[i].get("date") or ""))]


def report(rows):
    clouds = [cloud(record) for record in rows if cloud(record) is not None]
    months = sorted({str(record.get("date") or "")[:7] for record in rows if record.get("date")})
    return {
        "total": len(rows),
        "downloaded": sum(record.get("status") == "Downloaded" for record in rows),
        "failed": sum(str(record.get("status", "")).upper().startswith("FAILED") for record in rows),
        "cloud_mean": round(sum(clouds) / len(clouds), 2) if clouds else None,
        "cloud_min": min(clouds) if clouds else None,
        "cloud_max": max(clouds) if clouds else None,
        "months_covered": len(months),
        "months": months,
        "providers": dict(Counter(record.get("provider") for record in rows)),
    }
