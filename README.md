# EOChrono

Satellite image discovery, temporal scene selection, download tracking, and raster processing for QGIS.

[![Version](https://img.shields.io/badge/version-7.0.0-blue.svg)](https://github.com/abotalebmostafa11/EOChrono)
[![QGIS](https://img.shields.io/badge/QGIS-3.28--3.99-green.svg)](https://qgis.org/)
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

EOChrono is a Python plugin for QGIS that supports Earth observation scene discovery, quality-based ranking, temporal scene selection, resilient downloading, local inventory management, and raster-processing operations.

The software is designed for workflows in which researchers need to build traceable satellite-image collections while preserving the relationship between acquisition dates, scene quality, selected products, downloaded files, and downstream processing.

Repository: https://github.com/abotalebmostafa11/EOChrono

Version described here: `7.0.0`

## Main capabilities

EOChrono combines the following functions in one QGIS workflow.

- Search satellite catalogues using a polygon area of interest.
- Search Sentinel-1 and Sentinel-2 through the Copernicus Data Space Ecosystem.
- Search Landsat 7, Landsat 8, Landsat 9, and selected MODIS collections through STAC.
- Filter scenes using acquisition dates and cloud-cover thresholds.
- Remove duplicate scene records.
- Rank scenes by cloud quality, configured coverage, or a balanced score.
- Select the best scenes by score.
- Select one best scene per calendar month.
- Build temporally distributed image series with a greedy date-spacing strategy.
- Download selected products with retry, resume, cancellation, and concurrent-transfer support.
- Maintain CSV inventories and JSON metadata records.
- Save and restore EOChrono project settings.
- Clip, mosaic, and reproject raster data using QGIS Processing and GDAL providers.
- Calculate common spectral indices from prepared raster bands.

## Supported data sources

| Source | Catalogue | Configured collection or product filter |
|---|---|---|
| Sentinel-1 | Copernicus Data Space OData | `SENTINEL-1`, product names containing `IW_GRDH_1S` |
| Sentinel-2 | Copernicus Data Space OData | `SENTINEL-2`, product names containing `MSIL2A` |
| Landsat 7 | Planetary Computer STAC | `landsat-c2-l2`, platform `landsat-7` |
| Landsat 8 | Planetary Computer STAC | `landsat-c2-l2`, platform `landsat-8` |
| Landsat 9 | Planetary Computer STAC | `landsat-c2-l2`, platform `landsat-9` |
| MODIS MOD09A1 | Planetary Computer STAC | `modis-09A1-061` |
| MODIS MOD13Q1 | Planetary Computer STAC | `modis-13Q1-061` |
| MODIS MOD11A2 | Planetary Computer STAC | `modis-11A2-061` |
| MODIS MOD10A2 | Planetary Computer STAC | `modis-10A2-061` |

These entries describe the catalogue targets configured in version 7.0.0. They do not imply that every remote asset path has been validated under every provider configuration.

## Software workflow

A typical EOChrono workflow is:

1. Load or select a polygon area of interest.
2. Select a satellite source.
3. Define the acquisition-date interval.
4. Set the cloud-cover threshold and result limit.
5. Authenticate with Copernicus Data Space when using Sentinel searches.
6. Search the configured catalogue.
7. Inspect the returned scene table.
8. Apply a scene-selection strategy.
9. Download selected products.
10. Retain the CSV inventory and JSON metadata.
11. Prepare required raster bands.
12. Run clipping, mosaicking, reprojection, or spectral-index calculations in QGIS.

## Scene ranking

EOChrono currently exposes three ranking modes.

### Lowest cloud

For a scene with cloud percentage `c`, the quality score is

```text
Q = 100 - c
```

Cloud percentage is limited to the interval from 0 to 100.

If cloud information is missing, the implementation assigns a quality value of 50.

### AOI coverage

The coverage mode uses the scene `coverage` field.

In version 7.0.0, both provider adapters currently assign

```text
coverage = 100
```

Therefore, this field does not yet represent the true fraction of the study area covered by the scene.

### Balanced score

The balanced score is

```text
Q = 0.65 × cloud_quality + 0.35 × coverage
```

where

```text
cloud_quality = 100 - cloud_percentage
```

and missing cloud information gives a cloud-quality value of 50.

Because the current provider adapters assign coverage equal to 100, balanced ranking is currently driven mainly by cloud quality.

## Temporal scene selection

EOChrono includes three scene-selection strategies.

### Top-count selection

The requested number of scenes is selected by descending ranking score.

### Monthly selection

Scenes are grouped by calendar month and the highest-scoring scene is retained from each represented month.

### Time-series selection

EOChrono uses a greedy temporal-selection rule that combines scene quality with separation from dates already selected.

For each remaining candidate, the priority is

```text
priority = quality_score + 0.35 × min(date_spacing_days, 120)
```

The first iteration assigns the same spacing value to all candidates. After the first scene is selected, `date_spacing_days` is the minimum absolute date difference between a candidate and any scene already selected.

The spacing contribution is therefore capped at 42 score units.

This heuristic encourages temporal spread while retaining scene quality. It does not guarantee a globally optimal series, equal temporal spacing, or representation of every month.

## Reproducible selection example

The selection functions in version 7.0.0 were evaluated on six artificial records.

| Scene | Date | Cloud cover | Balanced score | Top 3 | Temporal 3 | Monthly |
|---|---:|---:|---:|:---:|:---:|:---:|
| S1 | 2024-01-01 | 0% | 100.00 | Yes | Yes | Yes |
| S2 | 2024-01-03 | 1% | 99.35 | Yes | No | No |
| S3 | 2024-01-05 | 2% | 98.70 | Yes | No | No |
| S4 | 2024-03-01 | 12% | 92.20 | No | Yes | Yes |
| S5 | 2024-05-01 | 18% | 88.30 | No | Yes | Yes |
| S6 | 2024-07-01 | 20% | 87.00 | No | No | Yes |

Observed results:

| Selection method | Selected scenes | Mean cloud cover | Acquisition span | Represented months |
|---|---|---:|---:|---:|
| Top-count | S1, S2, S3 | 1.0% | 4 days | 1 |
| Temporal | S1, S4, S5 | 10.0% | 121 days | 3 |
| Monthly | S1, S4, S5, S6 | 12.5% | 182 days | 4 |

The example demonstrates the intended tradeoff. Minimizing cloud cover alone can concentrate selected scenes within a short interval. Adding temporal separation can increase temporal representation while accepting scenes with higher cloud cover.

The example is artificial and should not be interpreted as an operational benchmark.

## Download management

The downloader in version 7.0.0 provides:

- HTTP streaming in 1 MiB chunks.
- Up to five download attempts.
- Exponential retry delays.
- HTTP range requests for conditional resume.
- Cancellation checks during transfer.
- Concurrent downloads.
- A default of four concurrent transfers in the interface.
- A selectable worker range from one to twelve.

For STAC records, EOChrono selects one asset for a scene according to an internal preference order. A downloaded STAC asset can therefore be a preview or a single science band rather than a complete multispectral product.

## Local records

EOChrono writes a CSV inventory containing the following fields:

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

EOChrono project files store search settings, download settings, and scene records in JSON format.

## Raster processing

EOChrono wraps QGIS Processing and GDAL operations for:

- Raster clipping by mask.
- Raster mosaicking.
- Raster reprojection.
- Adding generated raster layers to the active QGIS project.
- Batch spectral-index calculation through core helpers.
- Raster-information inspection through a core helper.

The interface reprojection action currently targets `EPSG:4326`. The underlying core function accepts a CRS argument.

## Spectral indices

EOChrono version 7.0.0 contains expressions for eight spectral indices.

| Index | Expression |
|---|---|
| NDVI | `(NIR - RED) / (NIR + RED)` |
| NDWI | `(GREEN - NIR) / (GREEN + NIR)` |
| MNDWI | `(GREEN - SWIR1) / (GREEN + SWIR1)` |
| NDMI | `(NIR - SWIR1) / (NIR + SWIR1)` |
| NDBI | `(SWIR1 - NIR) / (SWIR1 + NIR)` |
| SAVI | `1.5 × (NIR - RED) / (NIR + RED + 0.5)` |
| EVI | `2.5 × (NIR - RED) / (NIR + 6 × RED - 7.5 × BLUE + 1)` |
| BSI | `((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))` |

The index routine recursively searches `.tif`, `.tiff`, or `.vrt` files using configured filename aliases and uses band 1 from each matched raster.

Input bands must already be prepared, aligned, and appropriate for the selected sensor.

## Requirements

EOChrono is designed for QGIS Desktop with Python 3.

Plugin metadata for version 7.0.0 declares:

```text
Minimum QGIS version: 3.28
Maximum QGIS version: 3.99
```

Main runtime requirements include:

- QGIS Desktop.
- Python 3 provided by QGIS.
- PyQGIS.
- Qt through `qgis.PyQt`.
- `requests`.
- QGIS native Processing provider.
- GDAL Processing provider.
- Network access to the configured catalogue services.

## Installation

### Install from a release ZIP

When a packaged EOChrono release ZIP is available:

1. Download the EOChrono release ZIP.
2. Open QGIS.
3. Select `Plugins` > `Manage and Install Plugins`.
4. Open `Install from ZIP`.
5. Select the downloaded archive.
6. Install the plugin.
7. Enable EOChrono from the installed plugins list.

The ZIP should contain a valid QGIS plugin directory with `metadata.txt`, `__init__.py`, the plugin entry point, interface module, core modules, and required resources.

### Manual developer installation

Clone the repository:

```bash
git clone https://github.com/abotalebmostafa11/EOChrono.git
```

Place the EOChrono plugin directory inside the active QGIS profile plugin directory.

Typical locations are:

```text
Windows
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\

Linux
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/

macOS
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

Restart QGIS and enable the plugin.

## Basic use

### 1. Define the area of interest

Use a polygon layer already loaded in QGIS or browse to a supported vector file.

The software transforms the area of interest to EPSG:4326 before transmitting the geometry to catalogue services.

### 2. Configure the search

Choose:

- Satellite or product family.
- Start date.
- End date.
- Cloud threshold.
- Search result limit.
- Ranking mode.

### 3. Authenticate when required

Sentinel searches use Copernicus Data Space authentication.

Enter the required account credentials in the plugin authentication tab before searching Sentinel products.

Do not commit credentials or tokens to the repository.

### 4. Search and inspect scenes

Returned records are mapped to a common internal representation that includes identifiers, acquisition dates, cloud information, provider information, asset metadata, and download state.

### 5. Select scenes

Use one of the available approaches:

- Select records manually.
- Select the highest-ranked scenes.
- Apply monthly selection.
- Apply temporal time-series selection.

### 6. Download

Choose an output directory and download the checked scenes.

The plugin updates the inventory as download states change.

### 7. Process imagery

Prepare the sensor bands required by the selected spectral index, then use the processing tools for clipping, mosaicking, reprojection, or index calculation.

## Project structure

Version 7.0.0 is organized around a QGIS plugin entry point, a Qt interface module, and separate core modules.

```text
EOChrono/
├── __init__.py
├── geoimage_manager.py
├── ui_dialog.py
├── metadata.txt
├── icon.png
├── README.md
└── core/
    ├── __init__.py
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

The reviewed version contains 13 Python files.

## Current limitations

Version 7.0.0 has several known limitations that are relevant for scientific use.

- Provider adapters currently assign AOI coverage equal to 100 instead of calculating true polygon-scene intersection coverage.
- Missing cloud-cover values remain eligible after cloud filtering.
- Landsat 7, 8, and 9 share one STAC collection and platform filtering occurs after retrieval.
- Planetary Computer asset signing is not implemented.
- STAC downloading selects one asset and does not automatically assemble all bands required for multispectral analysis.
- A selected STAC asset may be a visual preview rather than a science band.
- Archive extraction is not implemented.
- JPEG2000 discovery is not implemented by the index routine.
- Raster index calculation does not apply sensor-specific scale factors or offsets.
- Filename aliases are shared and should not be treated as a universal sensor-band mapping.
- Download verification checks file existence and nonzero size in the interface but does not compare a trusted checksum.
- A SHA-256 helper exists but is not integrated into end-to-end transfer validation.
- Project files do not store the area-of-interest geometry itself.
- The current project loader does not fully restore every interface choice.
- Raster-processing functions require operational validation with declared QGIS versions and reference datasets.

These limitations should be considered when EOChrono is used in a reproducible scientific workflow.

## Reproducibility recommendations

For research use, record at least:

- EOChrono version.
- QGIS version.
- Operating system.
- Area-of-interest geometry.
- Catalogue source.
- Search date range.
- Cloud threshold.
- Ranking mode.
- Scene identifiers.
- Selected assets.
- Input band preparation steps.
- Applied scale factors and offsets.
- Processing CRS.
- Final output file names.

For an archival software release, create a tagged GitHub release such as `v7.0.0` and archive that exact release in a service that provides a persistent DOI.

## Citation

If you use EOChrono in research, cite the software repository and the associated software article when it becomes available.

Suggested software citation:

```text
Abotaleb, M. (2026). EOChrono: Satellite image discovery and temporal scene selection in QGIS. Version 7.0.0. https://github.com/abotalebmostafa11/EOChrono
```

BibTeX:

```bibtex
@software{abotaleb_eochrono_2026,
  author  = {Mostafa Abotaleb},
  title   = {EOChrono: Satellite Image Discovery and Temporal Scene Selection in QGIS},
  year    = {2026},
  version = {7.0.0},
  url     = {https://github.com/abotalebmostafa11/EOChrono}
}
```

Associated manuscript:

```text
EOChrono for satellite image discovery and temporal scene selection in QGIS
```

The final journal citation and DOI should be added here after publication.

## Funding

This work was funded by the Foundation for Scientific and Technological Development of Yugra under project No. 2026-252-01.

Project title:

> Development of a geoinformation system based on artificial intelligence methods for monitoring and forecasting waterlogging, bogging, and degradation of forest-marsh territories of the Khanty-Mansi Autonomous Okrug — Yugra.

## Author and support

Mostafa Abotaleb  
Engineering School of Digital Technologies  
Yugra State University  
Khanty-Mansiysk, Russia

Support email: `abotalebmostafa@bk.ru`

GitHub: https://github.com/abotalebmostafa11

## License

EOChrono is distributed under the MIT License.

See [LICENSE](LICENSE) for the complete license text.

Copyright © 2026 Abotaleb Mostafa.

## External services and documentation

EOChrono interacts with external services maintained by their respective organizations.

- QGIS: https://qgis.org/
- QGIS documentation: https://docs.qgis.org/
- Copernicus Data Space Ecosystem: https://dataspace.copernicus.eu/
- Copernicus Data Space API documentation: https://documentation.dataspace.copernicus.eu/APIs/OData.html
- STAC specification: https://stacspec.org/
- Microsoft Planetary Computer: https://planetarycomputer.microsoft.com/
- Landsat documentation: https://www.usgs.gov/landsat-missions

Availability, authentication rules, catalogue schemas, and external APIs can change independently of EOChrono.

## Contributing

Issues and pull requests are welcome through the GitHub repository.

When reporting a problem, include:

- EOChrono version.
- QGIS version.
- Operating system.
- Data source.
- Processing step.
- Error message.
- Minimal steps needed to reproduce the issue.

Please do not include usernames, passwords, access tokens, or other credentials in issue reports.
