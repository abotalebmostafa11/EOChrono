# Contributing to EOChrono

Contributions are welcome through GitHub issues and pull requests.

## Before opening an issue

Include:

- EOChrono version
- QGIS version
- Operating system
- Data source or catalogue
- Exact processing step
- Error message
- Minimal steps needed to reproduce the problem

Do not include passwords, tokens, API credentials or private datasets.

## Development setup

The deterministic scene-selection and inventory modules can be tested with standard Python.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

QGIS-dependent modules must be tested inside a compatible QGIS Python environment.

## Pull requests

Keep each pull request focused on one change.

When changing scene-selection logic:

1. Add or update tests.
2. Update the reproducibility example if its expected result changes.
3. Update `CHANGELOG.md`.
4. Explain the scientific or software reason for the change.

When changing catalogue adapters or raster processing:

1. State the provider or QGIS version used.
2. Record any API assumptions.
3. Avoid committing credentials.
4. Add a reproducible test or documented validation procedure where practical.

## Coding expectations

- Keep deterministic logic separate from the graphical interface where possible.
- Preserve readable CSV and JSON outputs.
- Avoid silent changes to scientific formulas.
- Document sensor-specific scale factors and band mappings.
- Keep backward compatibility in mind for project files and inventories.
