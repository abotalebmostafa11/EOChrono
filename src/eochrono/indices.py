from pathlib import Path
import re

INDEX_FORMULAS = {
    "NDVI": "(NIR-RED)/(NIR+RED)",
    "NDWI": "(GREEN-NIR)/(GREEN+NIR)",
    "MNDWI": "(GREEN-SWIR1)/(GREEN+SWIR1)",
    "NDMI": "(NIR-SWIR1)/(NIR+SWIR1)",
    "NDBI": "(SWIR1-NIR)/(SWIR1+NIR)",
    "SAVI": "1.5*((NIR-RED)/(NIR+RED+0.5))",
    "BSI": "((SWIR1+RED)-(NIR+BLUE))/((SWIR1+RED)+(NIR+BLUE))",
    "EVI": "2.5*((NIR-RED)/(NIR+6*RED-7.5*BLUE+1))",
}

BAND_ALIASES = {
    "BLUE": ["B02", "B2", "SR_B2", "BAND2"],
    "GREEN": ["B03", "B3", "SR_B3", "BAND3"],
    "RED": ["B04", "B4", "SR_B4", "BAND4"],
    "NIR": ["B08", "B8", "SR_B5", "BAND5"],
    "SWIR1": ["B11", "B6", "SR_B6", "BAND6"],
}


def find_band(folder, aliases):
    """Find a TIFF/VRT file whose stem contains one of the band aliases."""
    candidates = []
    for path in Path(folder).rglob("*"):
        if path.suffix.lower() not in (".tif", ".tiff", ".vrt"):
            continue
        stem = path.stem.upper()
        if any(re.search(rf"(^|[_\-.]){re.escape(alias)}([_\-.]|$)", stem) for alias in aliases):
            candidates.append(path)
    return sorted(candidates, key=lambda path: len(path.name))[0] if candidates else None
