# Changelog

All notable public changes to EOChrono are documented here.

## 7.0.0

Initial public research-software release.

### Added

- QGIS plugin interface for Earth observation workflows.
- Copernicus Data Space OData search for Sentinel-1 and Sentinel-2.
- STAC search for Landsat 7, 8 and 9 and selected MODIS collections.
- Scene deduplication and cloud-threshold filtering.
- Lowest-cloud, coverage and balanced ranking modes.
- Top-count scene selection.
- Monthly best-scene selection.
- Greedy temporal scene selection combining quality and date separation.
- Concurrent downloads with retry, conditional resume and cancellation.
- CSV inventory and JSON metadata output.
- Project persistence helpers.
- Raster clipping, mosaicking and reprojection through QGIS Processing.
- Eight spectral-index expressions.
- Reproducible six-scene temporal-selection example.
- Automated tests for deterministic selection and inventory functions.

### Known limitations

See `README.md` and `docs/USER_GUIDE.md` for the limitations of version 7.0.0.
