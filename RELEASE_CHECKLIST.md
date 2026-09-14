# Release Checklist

Use this checklist before creating the EOChrono `v7.0.0` GitHub release.

- [ ] Confirm the public software name is EOChrono.
- [ ] Confirm `EOChrono/metadata.txt` reports version 7.0.0.
- [ ] Confirm authors and support email.
- [ ] Run `python -m pytest -q`.
- [ ] Run `python examples/temporal_selection_example.py`.
- [ ] Open the plugin in a declared QGIS version.
- [ ] Verify search behavior for each provider you claim as operational.
- [ ] Verify no passwords, access tokens or private URLs are committed.
- [ ] Confirm the MIT license is approved by the software rights holder(s).
- [ ] Update `CHANGELOG.md`.
- [ ] Update `CITATION.cff`.
- [ ] Create Git tag `v7.0.0`.
- [ ] Create a GitHub Release from tag `v7.0.0`.
- [ ] Add the release URL to the Software Impacts manuscript.
- [ ] Archive the release with a DOI service if required.
- [ ] Add the final article DOI to the README after publication.
