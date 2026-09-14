# Developer Guide

## Architecture

The plugin is divided into a QGIS entry point, a Qt dialog and core modules.

```text
EOChrono/
├── __init__.py
├── geoimage_manager.py
├── ui_dialog.py
└── core/
    ├── auth.py
    ├── downloader.py
    ├── geometry.py
    ├── inventory.py
    ├── processing.py
    ├── project.py
    ├── providers.py
    ├── quality.py
    └── search.py
```

## Deterministic modules

`core/quality.py` contains scene scoring, deduplication and selection logic.

`core/inventory.py` contains CSV and JSON record-writing functions.

These modules can be tested without QGIS.

## QGIS-dependent modules

Geometry, interface and raster-processing functions require a QGIS Python environment.

Do not treat passing standard Python tests as validation of the full QGIS plugin.

## Adding a provider

A provider adapter should map external catalogue records into the common scene representation used by the interface and selection functions.

At minimum, preserve fields needed by downstream logic:

```text
id
name
date
cloud
provider
platform
url
assets
coverage
```

Document:

- endpoint
- collection identifier
- authentication requirement
- cloud field mapping
- platform mapping
- asset selection assumptions
- pagination behavior

## Changing selection logic

Selection changes should include:

- a deterministic test
- an example showing the changed behavior
- an update to `docs/REPRODUCIBILITY.md`
- an entry in `CHANGELOG.md`

Scientific formulas should not change silently.

## Release preparation

Before creating a release:

1. Run `python -m pytest -q`.
2. Run `python examples/temporal_selection_example.py`.
3. Verify `metadata.txt`.
4. Verify the plugin opens in the declared QGIS version.
5. Confirm that no credentials are present.
6. Update `CHANGELOG.md`.
7. Update `CITATION.cff`.
8. Tag the release.
