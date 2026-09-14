# Installation

## Requirements

EOChrono 7.0.0 declares compatibility with QGIS 3.28 through 3.99.

Required environment:

- QGIS Desktop
- Python 3 provided by QGIS
- PyQGIS
- Qt through `qgis.PyQt`
- `requests`
- QGIS native Processing provider
- GDAL Processing provider

## Install from a QGIS plugin ZIP

A QGIS plugin ZIP should contain a top-level `EOChrono` directory with at least:

```text
EOChrono/
├── __init__.py
├── metadata.txt
├── geoimage_manager.py
├── ui_dialog.py
├── icon.png
└── core/
```

In QGIS:

1. Open `Plugins`.
2. Open `Manage and Install Plugins`.
3. Choose `Install from ZIP`.
4. Select the EOChrono release ZIP.
5. Install and enable the plugin.

## Manual developer installation

Clone the repository:

```bash
git clone https://github.com/abotalebmostafa11/EOChrono.git
```

Copy the repository's `EOChrono` directory into the active QGIS profile plugin directory.

Typical plugin paths:

```text
Windows
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\

Linux
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/

macOS
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

Restart QGIS and enable EOChrono.

## Verify installation

After enabling the plugin:

- Confirm that an `EOChrono` menu entry appears.
- Open the plugin dialog.
- Confirm that the title displays `EOChrono 7.0.0`.
- Confirm that the QGIS Processing framework and GDAL provider are available before using raster-processing functions.

## Network access

Catalogue and download operations require network access to the configured external services.

Sentinel searches require valid Copernicus Data Space credentials. Never store credentials in the repository.
