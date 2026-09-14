import json
from qgis.core import QgsVectorLayer,QgsCoordinateReferenceSystem,QgsCoordinateTransform,QgsProject,QgsGeometry

def load_aoi(path):
    layer=QgsVectorLayer(path,"EOChrono_AOI","ogr")
    if not layer.isValid() or layer.geometryType()!=2: raise ValueError("AOI must be a valid polygon layer")
    return layer

def geometry_wgs84(layer):
    geom=None
    for f in layer.getFeatures():
        g=f.geometry()
        if g and not g.isEmpty(): geom=g if geom is None else geom.combine(g)
    if geom is None or geom.isEmpty(): raise ValueError("AOI has no geometry")
    if layer.crs().authid()!="EPSG:4326":
        geom.transform(QgsCoordinateTransform(layer.crs(),QgsCoordinateReferenceSystem("EPSG:4326"),QgsProject.instance()))
    return geom

def geojson_geometry(layer): return json.loads(geometry_wgs84(layer).asJson())
