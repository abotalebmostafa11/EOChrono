# Reproducibility

EOChrono 7.0.0 includes a deterministic example that reproduces the scene-selection results described in the Software Impacts manuscript.

The example does not require QGIS, satellite imagery, credentials or network access.

## Files

```text
examples/
├── example_scenes.csv
├── expected_selection_results.json
└── temporal_selection_example.py
```

The script loads the real implementation from:

```text
EOChrono/core/quality.py
```

## Run the example

From the repository root:

```bash
python examples/temporal_selection_example.py
```

Expected selected scene identifiers:

```text
Top-count: S1, S2, S3
Temporal:  S1, S4, S5
Monthly:   S1, S4, S5, S6
```

Expected summary values:

```text
Top-count mean cloud: 1.0%
Top-count acquisition span: 4 days

Temporal mean cloud: 10.0%
Temporal acquisition span: 121 days

Monthly mean cloud: 12.5%
Monthly acquisition span: 182 days
```

The script verifies the calculated result against `expected_selection_results.json`. A mismatch exits with an error.

## Run automated tests

Install the development test dependency:

```bash
python -m pip install -r requirements-dev.txt
```

Then run:

```bash
python -m pytest -q
```

These tests cover deterministic selection, scoring, deduplication and CSV/JSON inventory behavior.

They do not validate:

- the QGIS graphical interface
- remote authentication
- external catalogue availability
- real downloads
- QGIS raster-calculator execution
- GDAL processing outputs

Those functions require a declared QGIS environment and appropriate external services or reference datasets.

## Recommended archival workflow

For the article-associated release:

1. Commit the final source and reproducibility files.
2. Create the tag `v7.0.0`.
3. Create a GitHub Release from that tag.
4. Archive the exact release with a DOI-granting repository such as Zenodo if desired.
5. Add the version-specific release URL and DOI to the manuscript and `CITATION.cff`.
