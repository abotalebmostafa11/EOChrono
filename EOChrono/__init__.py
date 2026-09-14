def classFactory(iface):
    from .geoimage_manager import GeoImageManager
    return GeoImageManager(iface)
