"""QGIS integration helpers for EOChrono.

These modules require a Python environment provided by QGIS/PyQGIS.
"""


def available():
    try:
        import qgis  # noqa: F401
    except ImportError:
        return False
    return True
