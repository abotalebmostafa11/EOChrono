from ..catalog import PROVIDERS, normalize_cdse, normalize_stac, search_cdse, search_stac
from .geometry import geojson_geometry, geometry_wgs84


def search_provider(name, start, end, layer, limit=1000, token=None):
    config = PROVIDERS[name]
    if config["type"] == "cdse":
        wkt = geometry_wgs84(layer).asWkt()
        rows = search_cdse(
            config["collection"],
            config["contains"],
            start,
            end,
            wkt,
            limit=limit,
            token=token,
        )
        return [normalize_cdse(row, name) for row in rows]

    rows = search_stac(config["collections"], start, end, geojson_geometry(layer), limit=limit)
    out = []
    for feature in rows:
        platform = str(feature.get("properties", {}).get("platform", "")).lower()
        if config.get("platform") and platform != config["platform"]:
            continue
        out.append(normalize_stac(feature, name))
    return out[:limit]
