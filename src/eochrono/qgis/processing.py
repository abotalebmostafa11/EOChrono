from pathlib import Path

from ..indices import BAND_ALIASES, INDEX_FORMULAS, find_band


def calculate_index(folder, name, output=None):
    if name not in INDEX_FORMULAS:
        raise ValueError(f"Unsupported index: {name}")
    from qgis import processing
    from qgis.core import QgsRasterLayer

    required = {
        "NDVI": ["NIR", "RED"],
        "NDWI": ["GREEN", "NIR"],
        "MNDWI": ["GREEN", "SWIR1"],
        "NDMI": ["NIR", "SWIR1"],
        "NDBI": ["SWIR1", "NIR"],
        "SAVI": ["NIR", "RED"],
        "BSI": ["SWIR1", "RED", "NIR", "BLUE"],
        "EVI": ["NIR", "RED", "BLUE"],
    }[name]

    bands = {key: find_band(folder, BAND_ALIASES[key]) for key in required}
    missing = [key for key, value in bands.items() if not value]
    if missing:
        raise RuntimeError("Missing bands: " + ", ".join(missing))

    layers = []
    expression = INDEX_FORMULAS[name]
    for key, path in bands.items():
        layer = QgsRasterLayer(str(path), path.stem)
        if not layer.isValid():
            raise RuntimeError(f"Invalid raster: {path}")
        layers.append(layer)
        expression = expression.replace(key, f'"{layer.name()}@1"')

    out = Path(output or Path(folder) / (name + ".tif"))
    out.parent.mkdir(parents=True, exist_ok=True)
    processing.run(
        "native:rastercalc",
        {
            "LAYERS": layers,
            "EXPRESSION": expression,
            "CRS": layers[0].crs(),
            "EXTENT": layers[0].extent(),
            "CELL_SIZE": layers[0].rasterUnitsPerPixelX(),
            "OUTPUT": str(out),
        },
    )
    return out


def clip_raster(input_path, aoi_path, output_path):
    from qgis import processing

    return processing.run(
        "gdal:cliprasterbymasklayer",
        {
            "INPUT": str(input_path),
            "MASK": str(aoi_path),
            "CROP_TO_CUTLINE": True,
            "KEEP_RESOLUTION": True,
            "OUTPUT": str(output_path),
        },
    )["OUTPUT"]


def reproject_raster(input_path, output_path, crs):
    from qgis import processing

    return processing.run(
        "gdal:warpreproject",
        {"INPUT": str(input_path), "TARGET_CRS": crs, "OUTPUT": str(output_path)},
    )["OUTPUT"]


def mosaic_rasters(inputs, output_path):
    from qgis import processing

    return processing.run(
        "gdal:merge",
        {"INPUT": [str(item) for item in inputs], "OUTPUT": str(output_path), "SEPARATE": False},
    )["OUTPUT"]


def add_raster(path, name=None):
    from qgis.core import QgsProject, QgsRasterLayer

    layer = QgsRasterLayer(str(path), name or Path(path).stem)
    if layer.isValid():
        QgsProject.instance().addMapLayer(layer)
        return layer
    return None


def batch_calculate_index(folders, name, output_root):
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    outputs = []
    for folder in folders:
        folder = Path(folder)
        try:
            outputs.append(calculate_index(folder, name, root / (folder.name + "_" + name + ".tif")))
        except Exception as exc:
            outputs.append({"folder": str(folder), "error": str(exc)})
    return outputs


def raster_info(path):
    from qgis.core import QgsRasterLayer

    layer = QgsRasterLayer(str(path), Path(path).stem)
    if not layer.isValid():
        raise RuntimeError(f"Invalid raster: {path}")
    return {
        "name": layer.name(),
        "crs": layer.crs().authid(),
        "width": layer.width(),
        "height": layer.height(),
        "bands": layer.bandCount(),
        "pixel_x": layer.rasterUnitsPerPixelX(),
        "pixel_y": layer.rasterUnitsPerPixelY(),
        "extent": layer.extent().toString(),
    }
