from __future__ import annotations

import requests

CDSE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"

PROVIDERS = {
    "Sentinel-1": {"type": "cdse", "collection": "SENTINEL-1", "contains": "IW_GRDH_1S"},
    "Sentinel-2": {"type": "cdse", "collection": "SENTINEL-2", "contains": "MSIL2A"},
    "Landsat-7": {"type": "stac", "collections": ["landsat-c2-l2"], "platform": "landsat-7"},
    "Landsat-8": {"type": "stac", "collections": ["landsat-c2-l2"], "platform": "landsat-8"},
    "Landsat-9": {"type": "stac", "collections": ["landsat-c2-l2"], "platform": "landsat-9"},
    "MODIS-MOD09A1": {"type": "stac", "collections": ["modis-09A1-061"], "platform": None},
    "MODIS-MOD13Q1": {"type": "stac", "collections": ["modis-13Q1-061"], "platform": None},
    "MODIS-MOD11A2": {"type": "stac", "collections": ["modis-11A2-061"], "platform": None},
    "MODIS-MOD10A2": {"type": "stac", "collections": ["modis-10A2-061"], "platform": None},
}


def _get_json(url, *, params=None, headers=None, timeout=120):
    response = requests.get(url, params=params, headers=headers or {}, timeout=timeout)
    response.raise_for_status()
    return response.json()


def search_cdse(collection, contains, start, end, geometry_wkt, *, limit=1000, token=None):
    filters = [
        f"Collection/Name eq '{collection}'",
        f"contains(Name,'{contains}')",
        f"ContentDate/Start ge {start}T00:00:00.000Z",
        f"ContentDate/Start lt {end}T23:59:59.999Z",
        f"OData.CSC.Intersects(area=geography'SRID=4326;{geometry_wkt}')",
    ]
    headers = {"Authorization": "Bearer " + token} if token else {}
    rows = []
    skip = 0
    while len(rows) < limit:
        top = min(1000, limit - len(rows))
        params = {
            "$filter": " and ".join(filters),
            "$orderby": "ContentDate/Start asc",
            "$top": top,
            "$skip": skip,
        }
        batch = _get_json(CDSE_URL, params=params, headers=headers).get("value", [])
        rows.extend(batch)
        if len(batch) < top:
            break
        skip += len(batch)
    return rows[:limit]


def search_stac(collections, start, end, intersects, *, limit=1000, query=None):
    payload = {
        "collections": list(collections),
        "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z",
        "intersects": intersects,
        "limit": min(100, limit),
    }
    if query:
        payload["query"] = query
    rows = []
    url = STAC_URL
    first = True
    while url and len(rows) < limit:
        if first:
            response = requests.post(url, json=payload, timeout=120)
            first = False
        else:
            response = requests.get(url, timeout=120)
        response.raise_for_status()
        data = response.json()
        rows.extend(data.get("features", []))
        url = next((link.get("href") for link in data.get("links", []) if link.get("rel") == "next"), None)
    return rows[:limit]


def normalize_cdse(product, provider_name):
    attrs = {item.get("Name"): item.get("Value") for item in product.get("Attributes", [])}
    product_id = product.get("Id")
    return {
        "id": product_id,
        "name": product.get("Name"),
        "date": product.get("ContentDate", {}).get("Start"),
        "cloud": attrs.get("cloudCover"),
        "size": product.get("ContentLength"),
        "provider": provider_name,
        "platform": provider_name,
        "url": f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value",
        "assets": {},
        "attributes": attrs,
        "coverage": 100,
        "asset_count": 0,
    }


def normalize_stac(feature, provider_name):
    props = feature.get("properties", {})
    assets = feature.get("assets", {})
    return {
        "id": feature.get("id"),
        "name": feature.get("id"),
        "date": props.get("datetime") or props.get("start_datetime"),
        "cloud": props.get("eo:cloud_cover"),
        "size": None,
        "url": None,
        "assets": assets,
        "provider": provider_name,
        "platform": props.get("platform"),
        "bbox": feature.get("bbox"),
        "properties": props,
        "coverage": 100,
        "asset_count": len(assets),
    }
