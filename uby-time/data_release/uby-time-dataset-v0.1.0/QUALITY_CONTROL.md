# Quality Control

The generated `quality_control_report.json` summarizes automated release checks.

## Automated checks

- Processed data directory exists.
- All manifest files are non-empty.
- SHA-256 checksums were generated for every archived processed file.
- CSV row counts were computed.
- SQLite table row counts were computed.
- JSON top-level keys were recorded.

## Summary

- CSV files: 12
- SQLite files: 13
- JSON files: 12
- Total CSV rows: 3,172,053
- Total SQLite table rows: 4,909,419

## Scientific limitations

This release is intended for reusable time-labeling, interoperability, and
hypothesis generation.  Some downstream scientific analyses, especially
mass-extinction timing claims, require additional uncertainty propagation,
collection-level standardization, subsampling, and domain-specialist validation.
