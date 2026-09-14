# EOChrono User Guide

## Purpose

EOChrono helps prepare traceable satellite-image collections in QGIS by combining catalogue search, scene ranking, temporal selection, downloading, inventories and selected raster-processing operations.

## Standard workflow

1. Load a polygon area of interest in QGIS.
2. Open EOChrono.
3. Choose a satellite or product family.
4. Set the start and end dates.
5. Set the cloud-cover threshold.
6. Choose a ranking mode.
7. Search the catalogue.
8. Inspect the returned scene records.
9. Select scenes manually or with a selection strategy.
10. Download selected records.
11. Retain the CSV inventory and JSON metadata.
12. Prepare required raster bands.
13. Use QGIS processing tools for clipping, mosaicking, reprojection or index calculation.

## Selection strategies

### Top-count

Returns the requested number of records with the highest score.

### Monthly

Groups scenes by calendar month and retains the highest-scoring scene in each represented month.

### Temporal time series

Uses a greedy rule that combines the ranking score with date separation from already selected scenes.

```text
priority = quality_score + 0.35 × min(date_spacing_days, 120)
```

This encourages a wider temporal spread. It does not guarantee globally optimal spacing.

## Local records

The inventory CSV stores:

```text
id
name
date
cloud
size
provider
platform
status
local_path
score
coverage
asset
url
```

Successful transfers can also receive a JSON metadata sidecar.

## Raster indices

The source contains expressions for:

- NDVI
- NDWI
- MNDWI
- NDMI
- NDBI
- SAVI
- EVI
- BSI

Input rasters must already be prepared and aligned. EOChrono 7.0.0 does not automatically apply sensor-specific radiometric scale factors or offsets.

## Important limitations in 7.0.0

- Provider adapters currently assign coverage equal to 100 rather than true AOI intersection coverage.
- Missing cloud values can remain eligible.
- Landsat platform filtering occurs after the shared STAC collection search.
- Planetary Computer asset signing is not implemented.
- STAC downloading chooses one asset and does not assemble all science bands.
- A chosen asset can be a preview.
- Archive extraction and JPEG2000 discovery are not implemented.
- Sensor-specific scale factors and offsets are not automatically applied.
- Shared filename aliases are not a universal band map for every sensor.
- End-to-end checksum validation is not implemented.
- Project files do not include the AOI geometry.
- QGIS-dependent processing requires operational validation for the exact QGIS environment used.

For scientific work, record EOChrono version, QGIS version, area of interest, catalogue, search interval, thresholds, ranking mode, scene identifiers, selected assets, band preparation and processing CRS.
