# Contributing to uby-time

`uby-time` is the Python reference implementation for the UBY Cross-scale Time Labeling Specification.

## Development setup

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

## Ground rules

- Keep implementation behavior aligned with `UBY-TLS-WD-0.1.0.md`.
- Do not introduce false precision.
- Do not treat UBY as an absolute physical time system.
- Do not use lookback time `t0 - t(z)` as a UBY value.
- Preserve `Decimal` values as strings in JSON serialization.
- Add tests for every behavior change.

## Pull request checklist

- Tests pass.
- Public API changes are documented.
- CLI behavior is covered by tests where practical.
- Any numerical behavior change includes a migration note in `CHANGELOG.md`.
