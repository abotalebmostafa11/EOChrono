import json

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsVectorLayer


def load_aoi(path):
    layer = QgsVectorLayer(path, "EOChrono_AOI", "ogr")
    if not layer.isValid() or layer.geometryType() != 2:
        raise ValueError("AOI must be a valid polygon layer")
    return layer


def geometry_wgs84(layer):
    geometry = None
    for feature in layer.getFeatures():
        current = feature.geometry()
        if current and not current.isEmpty():
            geometry = current if geometry is None else geometry.combine(current)
    if geometry is None or geometry.isEmpty():
        raise ValueError("AOI has no geometry")
    if layer.crs().authid() != "EPSG:4326":
        geometry.transform(
            QgsCoordinateTransform(
                layer.crs(),
                QgsCoordinateReferenceSystem("EPSG:4326"),
                QgsProject.instance(),
            )
        )
    return geometry


def geojson_geometry(layer):
    return json.loads(geometry_wgs84(layer).asJson())
