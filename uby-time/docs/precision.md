# Precision, Uncertainty, and Conformance

UBY uses three precision levels and a mandatory metadata discipline to prevent false precision.  UBY values are labels and indexes; they do not replace source time systems such as UTC, Julian Date, BP/Ma/Ga, chronostratigraphic vocabularies, or cosmological redshift.

The executable WD 0.1.0 conformance profile is exposed as:

```python
from uby_time import WD_0_1_0_PROFILE, validate_conformance_profile, is_conformant
```

## Level 1: relative precise measurement level

Level 1 covers approximately ±1,000,000 years around the civil / astronomical-year reference window.

It is suitable for:

- Gregorian / ISO date indexing;
- UTC / ISO 8601 event timestamps;
- Julian Date values;
- astronomical year labels;
- BC / AD mnemonic labels;
- near-present historical, geophysical, astronomical-discovery, and event-catalog data.

Required metadata:

- `uby_value`
- `uby_version`
- `precision_level`
- `source_time`
- `source_system`
- `rounding_rule`
- `generated_by`
- `anchor_id`
- `anchor_jd`
- `anchor_uby`

Recommended metadata:

- `uncertainty_years`
- `confidence_level`
- `propagation_note`

Level 1 false-precision rules:

- Year-only data must not be converted into a fabricated month/day/time.
- Calendar ambiguity must not be hidden.
- UTC/ISO-derived UBY labels must not be treated as legal time, financial time, navigation time, or precision-timing substitutes.

## Level 2: proportional narrative level

Level 2 is for proportional narrative and broad-scale time labels.

It is suitable for:

- geological and biological history timelines;
- chronostratigraphic boundaries;
- Ma BP / Ga BP values;
- fossil occurrence age intervals;
- paleoclimate age models;
- broad-scale educational diagrams;
- rough long-term archival indexes.

Required metadata:

- `uby_value`
- `uby_version`
- `model_version`
- `precision_level`
- `source_time`
- `source_system`
- `rounding_rule`
- `generated_by`
- `anchor_id`
- `anchor_jd`
- `anchor_uby`

Recommended metadata:

- `uncertainty_years`
- `interval_start_uby`
- `interval_end_uby`
- `uncertainty_kind`
- `propagation_note`

Level 2 rules:

- `model_version` is required.
- Records should carry `uncertainty_years` or interval bounds.
- Intervals must not be collapsed into exact instants without declaring the representative rule.
- Ma/Ga source precision must not be expanded into unsupported decimal places.
- Chronostratigraphic names must not be treated as exact numeric times.

## Level 3: model-dependent cosmological level

Level 3 applies to high-redshift, early-universe, cosmological-lookback, and other model-derived events.

It is suitable for:

- cosmological redshift values;
- model-derived lookback times;
- cosmological age estimates;
- early-universe event labels.

Required metadata:

- `uby_value`
- `uby_version`
- `model_version`
- `precision_level`
- `source_time`
- `source_system`
- `rounding_rule`
- `generated_by`
- `anchor_id`
- `anchor_jd`
- `anchor_uby`

Recommended metadata:

- `propagation_note`
- `uncertainty_years`
- `confidence_level`
- `interval_start_uby`
- `interval_end_uby`
- `uncertainty_kind`

Level 3 rules:

- `model_version` is required.
- Records should carry `uncertainty_years` or interval bounds.
- A `propagation_note` should describe conversion assumptions.
- Redshift-to-age conversion must not be reported without cosmological model metadata.
- Model-dependent values must not be compared as model-independent instants.
- Derived effective digits must not exceed source/model support.

## Uncertainty schema

UBY WD 0.1.0 recognizes these uncertainty kinds:

- `measurement`
- `temporal_resolution`
- `interval`
- `model`
- `observational`
- `propagated`
- `propagated_addition`
- `propagated_multiplication`

Rules:

- `uncertainty_years` is a non-negative decimal-string value when serialized.
- `confidence_level`, if present, must be in the closed interval `[0, 1]`.
- Missing uncertainty means unknown or undeclared uncertainty; it must not be interpreted as zero.
- A representative `uby_value` derived from an interval must preserve source interval or uncertainty metadata.
- The representative rule should be declared in `source_system` or `propagation_note`.

## Interval representation

UBY interval fields:

- `interval_start_uby`
- `interval_end_uby`

WD 0.1.0 treats these as a closed interval by default.

Rules:

- `interval_start_uby <= interval_end_uby`.
- `uby_value` may be a midpoint, boundary, or model-derived representative only if the rule is documented.
- Native interval fields must remain available through `source_time`, `source_system`, or dataset-level provenance.
- Interval metadata complements the representative UBY value; it does not replace the source record.

## Provenance model

Required provenance fields:

- `source_time`
- `source_system`
- `rounding_rule`
- `generated_by`
- `uby_version`
- `anchor_id`
- `anchor_jd`
- `anchor_uby`

Recommended provenance fields:

- `propagation_note`
- `model_version`
- `confidence_level`
- `uncertainty_kind`

Rules:

- `source_time` must preserve the native source time expression when available.
- `source_system` must identify the native or derived time system used for conversion.
- `generated_by` must identify the implementation and version that produced the record.

## Model dependency metadata

Level 2 and Level 3 records require `model_version`.

Recommended model-dependent metadata:

- `propagation_note`
- `uncertainty_years`
- `confidence_level`
- `interval_start_uby`
- `interval_end_uby`

Rules:

- Level 3 records should include model parameters or a resolvable model profile in `propagation_note` or dataset-level provenance.
- Any model-derived conversion should describe conversion method and assumptions.
- Different models may produce different UBY labels for the same source expression; this must remain visible.

## Anchor and version compatibility

Default WD 0.1.0 anchor:

- `anchor_iso`: `2026-01-01T00:00:00Z`
- `anchor_jd`: `2461041.5`
- `anchor_uby`: `13787002026.0`

Required anchor fields:

- `anchor_id`
- `anchor_jd`
- `anchor_uby`

Rules:

- `uby_version` must use semantic versioning.
- A record is comparable within a UBY series only when anchor fields and version semantics are compatible.
- Any future anchor change must use a new `anchor_id` and compatibility mapping.
- Existing serialized records must retain their original anchor fields.

## Conformance test suite

The reference implementation includes a conformance test suite in:

```text
tests/test_conformance_profiles.py
```

The suite verifies:

- formal Level 1/2/3 definitions;
- uncertainty schema;
- interval representation;
- provenance model;
- model dependency metadata;
- anchor/version compatibility;
- Level 1 conformant records;
- Level 2 model and uncertainty expectations;
- interval ordering;
- unknown uncertainty-kind warnings;
- Level 3 model propagation-note recommendation;
- spec-version mismatch warning.

Example:

```python
from uby_time import iso_to_uby, validate_conformance_profile, is_conformant

uby = iso_to_uby("2026-01-01T00:00:00Z", prefer_astropy=False)
messages = validate_conformance_profile(uby)

assert messages == []
assert is_conformant(uby)
```

## False precision

`uby-time` must not imply precision unsupported by source data.

Examples:

- Prefer `UBY 380K` over `UBY 380000.000000` for CMB decoupling when the source/model support is broad.
- Do not treat `z=0` cosmological age as identical to the Level 1 civil-date anchor.
- Do not interpret missing uncertainty as zero uncertainty.
- Do not convert a fossil occurrence interval into an exact instant without preserving the interval.
- Do not convert a discovery year into a fabricated precise timestamp.
