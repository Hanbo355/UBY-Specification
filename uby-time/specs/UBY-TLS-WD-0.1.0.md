# UBY Cross-scale Time Labeling Specification

**Universal Big-bang Year Cross-scale Time Labeling Specification**  
**UBY-TLS-WD-0.1.0**

| Item | Content |
| --- | --- |
| Document type | Technical standard working draft |
| Specification name | UBY Cross-scale Time Labeling Specification |
| Specification identifier | UBY-TLS |
| Current version | 0.1.0 |
| Release stage | Working Draft |
| Release date | 2026-06-15 |
| Scope of application | Cross-scale time labeling, long-term archival, auxiliary indexing for scientific data, and cosmological-geological-human-history narratives |
| Current status | Exploratory working draft; not yet a formal specification |
| DOI | 10.5281/zenodo.20763218 (dataset archive); specification DOI to be assigned |

---

## Copyright and Citation Notice

This specification defines the UBY cross-scale time labeling system. Implementers, researchers, and data publishers are encouraged to cite this specification as follows:

```text
UBY Cross-scale Time Labeling Specification, Working Draft 0.1.0.
```

When citing a specific expression, the specification version tag should also be retained:

```text
[spec=0.1.0]
```

---

## 0. Specification Status and Reading Conventions

### 0.1 Document Status

This document is **Working Draft 0.1.0**. This version fixes the initial concepts, terminology, notation, anchors, data fields, and reference implementation requirements for UBY.

This document does not constitute a formal international standard, national standard, industry standard, or authoritative scientific data specification. Future versions may adjust fields, algorithms, examples, conformance levels, or notation.

### 0.2 Normative Language

This document uses the following terms to express normative strength:

| Term | Meaning |
| --- | --- |
| MUST | An implementation or dataset claiming conformance to this specification is not allowed to violate the requirement |
| MUST NOT | An explicitly prohibited behavior |
| SHOULD | Strongly recommended unless there is a clear reason not to comply |
| MAY | An optional capability or permitted behavior |
| RECOMMENDED | Non-mandatory, but beneficial for interoperability and long-term maintenance |

### 0.3 Normative and Informative Content

Unless explicitly marked as informative, appendices, examples, and explanatory notes are normative when they appear in the main body of this document.

---

## 1. Abstract

UBY, the Universal Big-bang Year, is a conventional time-coordinate system for cross-scale time labeling. It uses the comoving-time origin in a cosmological model as the conventional zero point and the standard Julian year as the base unit, placing cosmic history, geological history, human history, and long-term future events on a monotonically increasing labeling axis.

UBY is not designed to replace existing time systems. Instead, it provides a unified, traceable, and versioned auxiliary time label for cross-scale visualization, long-term archival, data indexing, public-science narratives, and interdisciplinary data exchange.

UBY MUST NOT be interpreted as model-independent absolute physical time. The meaning of a UBY value depends on:

1. the UBY specification version used;
2. the cosmological model or anchor version used;
3. the source and precision of the native time data;
4. the precision level associated with the use case;
5. the rounding rule and uncertainty statement.

---

## 2. Scope

### 2.1 In Scope

This specification applies to the following scenarios:

1. unified labeling of cross-scale timelines spanning cosmic history, geological history, and human history;
2. auxiliary time indexing for long-duration data archives;
3. supplementary identifiers coexisting with native time fields in scientific datasets;
4. continuous time narratives in museums, education, public science, and digital humanities;
5. interdisciplinary documents that need to reference calendar dates, Julian Dates, geological ages, redshift, or cosmic age simultaneously;
6. auxiliary time anchors in records longer than ten thousand years, civilization archives, and ultra-long-term explanatory materials;
7. cross-scale time labels in software systems, databases, visualizations, and APIs.

### 2.2 Out of Scope

This specification MUST NOT be used for the following scenarios:

1. legal documents, contracts, financial settlement, administrative approval, or other contexts that depend on legally defined date and time;
2. satellite navigation, time transfer, aerospace telemetry and control, deep-space navigation, or other high-precision engineering contexts;
3. replacement of professional timekeeping systems such as atomic time, Coordinated Universal Time, or GNSS time;
4. the sole authoritative time record for raw astronomical, geological, or archaeological data;
5. engineering calculations requiring relativistic proper time, coordinate time, or orbital dynamics;
6. interpreting pre-Big-Bang time or cosmological singularities as directly measured physical time;
7. any context in which misuse of time information could create legal, safety, financial, or engineering risks.

### 2.3 Relationship to Existing Time Systems

UBY is a supplementary labeling layer. Formal data MUST retain native time representations, such as:

- UTC / TAI;
- ISO 8601;
- JD / MJD;
- geological ages or stratigraphic units;
- BP, ka, Ma, Ga;
- redshift z;
- original dating reports and associated uncertainties.

UBY MAY be added as an auxiliary field, but it MUST NOT delete or replace native time fields.

---

## 3. Normative References

The following documents are important references for this specification. Unless a version is explicitly specified, the latest valid version of the referenced document may be used as a reference.

1. ISO 8601:2019, *Date and time — Representations for information interchange*.
2. BIPM, *The International System of Units (SI)*, 9th edition, 2019.
3. International Astronomical Union, astronomical time scale and Julian Date conventions.
4. Planck Collaboration, *Planck 2018 results. VI. Cosmological parameters*, Astronomy & Astrophysics, 641, A6, 2020.
5. International Commission on Stratigraphy, *International Chronostratigraphic Chart*.
6. Seidelmann, P. K. (Ed.), *Explanatory Supplement to the Astronomical Almanac*, University Science Books, 1992.
7. McCarthy, D. D., & Seidelmann, P. K., *Time: From Earth Rotation to Atomic Physics*, Wiley-VCH, 2009.
8. RFC 5234, *Augmented BNF for Syntax Specifications: ABNF*.
9. Semantic Versioning 2.0.0.

---

## 4. Terms and Definitions

### 4.1 UBY

UBY, the Universal Big-bang Year, is a continuous time-labeling system that uses the comoving-time origin in a cosmological model as the conventional zero point and the standard Julian year as the unit.

A UBY value expresses the number of years elapsed since the conventional zero point.

### 4.2 UBY Expression

A UBY expression is a textual representation that conforms to the syntax of this specification, for example:

```text
UBY 13787002026 [model=LCDM-Planck2018] [spec=0.1.0]
```

### 4.3 UBY Value

The UBY value is the numeric part of a UBY expression, expressed in standard Julian years.

For example, the UBY value in the following expression is `13787002026`:

```text
UBY 13787002026 [spec=0.1.0]
```

### 4.4 Standard Julian Year

A standard Julian year is defined as:

```text
1 Julian year = 365.25 × 86400 s = 31557600 s
```

The base unit of UBY is the standard Julian year.

The standard Julian year is a constant definition. It is not the same as the actual terrestrial tropical year and does not change with long-term variations in Earth's rotation or orbit.

### 4.5 Cosmological Comoving Time

Cosmological comoving time is the time coordinate measured by ideal observers that move with the mean cosmic expansion in an FLRW cosmological model.

In UBY, comoving time is used only as a modeled labeling coordinate and does not constitute model-independent absolute time.

### 4.6 Model Version

The model version identifies the cosmological model, parameter source, parameter epoch, anchor, or revision information on which a UBY value depends.

The RECOMMENDED format is:

```text
[model=<model-family>-<source-or-parameter-set>[-<revision-id>]]
```

Examples:

```text
[model=LCDM-Planck2018]
[model=LCDM-WMAP9]
[model=LCDM-Planck2018-base]
[model=Custom-ArchiveA-2026]
```

### 4.7 Specification Version

The specification version identifies the syntax, fields, and interpretation rules followed by a UBY expression.

Example:

```text
[spec=0.1.0]
```

### 4.8 Anchor

An anchor is a conventional reference point used to align a UBY value with a native time system. An anchor normally includes:

- anchor identifier;
- native time;
- JD value;
- UBY value;
- model version;
- specification version.

### 4.9 Precision Level

The precision level describes the reliability source and applicable scope of a UBY value. This specification defines three levels:

1. Level 1: near-Earth relative metrological level;
2. Level 2: cross-scale proportional narrative level;
3. Level 3: cosmological-model-dependent level.

### 4.10 Uncertainty

Uncertainty expresses the error range, confidence level, or degree of model dependence of a UBY value. Uncertainty may originate from native measurements, model parameters, rounding rules, or combinations of multiple sources.

---

## 5. Design Principles

### 5.1 Supplementarity Principle

UBY MUST be used as a supplementary field to native time systems. It MUST NOT replace UTC, TAI, JD, geological timescales, redshift, or original dating results.

### 5.2 Model Transparency Principle

Any UBY value that depends on a cosmological model, parameter set, or anchor assumption MUST declare the model version or traceable anchor information.

### 5.3 No Precision Inflation Principle

A UBY output MUST NOT imply precision higher than that supported by the native source material or the model itself.

If the source material supports only million-year precision, the UBY expression MUST NOT be displayed with unsupported fractional-year, day-level, or second-level precision.

### 5.4 Version Traceability Principle

UBY expressions in formal data exchange and long-term archival SHOULD declare the specification version.

RECOMMENDED form:

```text
[spec=0.1.0]
```

### 5.5 Computable Interoperability Principle

Implementers MUST be able to reproduce UBY values from the anchor, unit, rounding rule, model version, and specification version.

### 5.6 Misuse Prohibition Principle

Implementations, documentation, and user interfaces MUST NOT describe UBY as:

- absolute time;
- an authoritative timekeeping system;
- a replacement for raw scientific data;
- a legal or financial time basis;
- a high-precision engineering time system.

---

## 6. Precision Levels

### 6.1 Overview

| Level | Name | Primary scope | Reliability source | Typical use | Limitation |
| --- | --- | --- | --- | --- | --- |
| Level 1 | Near-Earth relative metrological level | Approximately ±1,000,000 years around the Common Era | Native historical, astronomical, archaeological, geological, or dating data | Continuous numbering across BCE/CE, sorting, indexing | Does not increase source precision |
| Level 2 | Cross-scale proportional narrative level | Large-scale cosmic, Earth, and life-evolution events | Source version, model approximation, significant digits | Cross-scale presentation, public science, long-term archival | Not suitable for high-precision quantitative computation |
| Level 3 | Cosmological-model-dependent level | High-redshift, early-universe, and model-integrated events | Cosmological model and parameter set | Auxiliary cosmological labeling and within-model comparison | Values from different models are not directly comparable |

### 6.2 Level 1: Near-Earth Relative Metrological Level

Level 1 applies when the native time source is the Gregorian calendar, ISO 8601, JD, historical chronology, or near-Earth dating evidence.

In Level 1, UBY mainly provides continuous numbering and indexing across the BCE/CE boundary.

Implementers MUST note that:

1. UBY does not correct uncertainty in original historical sources;
2. BCE years MUST explicitly distinguish traditional BC numbering from ISO astronomical year numbering;
3. if the original date is imprecise, the output MUST NOT display false high precision;
4. Level 1 MAY omit the model tag, but formal data SHOULD still retain anchor or model information.

### 6.3 Level 2: Cross-scale Proportional Narrative Level

Level 2 applies to large-scale events such as Solar System formation, geological time intervals, life evolution, mass extinctions, and long-term future events.

Level 2 outputs SHOULD be displayed using appropriate significant digits.

Example:

```text
UBY 9.22G [model=LCDM-Planck2018] [spec=0.1.0]
```

It SHOULD NOT be written as:

```text
UBY 9220000000.000000 [model=LCDM-Planck2018] [spec=0.1.0]
```

unless the native source supports that precision.

### 6.4 Level 3: Cosmological-model-dependent Level

Level 3 applies to high-redshift and early-universe events, such as:

- cosmic microwave background decoupling;
- formation of the first generation of stars;
- high-redshift galaxies;
- cosmic age derived from redshift integration.

A Level 3 expression MUST declare the model version.

Example:

```text
UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]
```

Level 3 UBY values under different model versions MUST NOT be directly compared unless an explicit conversion method or recomputed result is provided.

---

## 7. Notation

### 7.1 General Structure

The general structure of a UBY expression is:

```text
UBY <value> [model=<model-id>] [spec=<spec-version>]
```

where:

- `UBY` is the fixed prefix;
- `<value>` is the UBY value;
- `[model=...]` is the model version tag;
- `[spec=...]` is the specification version tag.

### 7.2 Full Numeric Format

The full numeric format is used for computation, storage, databases, and formal exchange.

Syntax:

```text
UBY <decimal> [model=<model-id>] [spec=<spec-version>]
```

Examples:

```text
UBY 13787002026 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 13786999780 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 380000 [model=LCDM-Planck2018] [spec=0.1.0]
```

Rules:

1. thousand separators MUST NOT be used;
2. decimal places MUST NOT exceed the precision supported by the source material;
3. `[spec=...]` SHOULD be included in formal exchange;
4. Level 2 and Level 3 SHOULD include `[model=...]`;
5. Level 1 MAY omit `[model=...]` if the context has already declared the anchor.

### 7.3 Magnitude Shorthand Format

The magnitude shorthand format is used for display, charts, and public-science materials.

Syntax:

```text
UBY <number><scale> [model=<model-id>] [spec=<spec-version>]
```

Magnitude symbols:

| Symbol | Meaning | Multiplier |
| --- | --- | --- |
| K | thousand years | 10³ |
| M | million years | 10⁶ |
| G | billion years | 10⁹ |
| T | trillion years | 10¹² |

Examples:

```text
UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]
UBY 9.22G [model=LCDM-Planck2018] [spec=0.1.0]
UBY 13.787G [model=LCDM-Planck2018] [spec=0.1.0]
```

The magnitude shorthand format MUST NOT be used as the only long-term storage format.

### 7.4 Scientific Notation Format

Scientific notation is used to display very large or very small scales.

Syntax:

```text
UBY <coefficient>×10^<exponent> [model=<model-id>] [spec=<spec-version>]
```

Example:

```text
UBY 3.8×10^5 [model=LCDM-Planck2018] [spec=0.1.0]
```

In pure ASCII environments, `x` MAY be used instead of `×`:

```text
UBY 3.8x10^5 [model=LCDM-Planck2018] [spec=0.1.0]
```

### 7.5 Academic Mnemonic Format

The academic mnemonic format is used for human-readable Level 1 display.

Syntax:

```text
UBY <prefix><sign><year6> [model=<model-id>] [spec=<spec-version>]
```

where:

- `<prefix>` is a 6-digit mnemonic prefix;
- `<sign>` is `+` or `-`;
- `<year6>` is the 6-digit absolute value of the astronomical year.

Mnemonic prefix calculation rule:

```text
prefix = ROUND(t0_Ga × 10000)
```

where `t0_Ga` is the current age of the universe given by the model, in billions of years.

Planck 2018 example:

```text
t0_Ga = 13.787
prefix = ROUND(13.787 × 10000) = 137870
```

Examples:

```text
UBY 137870+002026 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]
```

The relationship between the mnemonic and the full numeric value is:

```text
UBY <P>+YYYYYY = UBY (P × 100000 + YYYYYY)
UBY <P>-YYYYYY = UBY (P × 100000 - YYYYYY)
```

Examples:

```text
UBY 137870+002026 [spec=0.1.0] = UBY 13787002026 [spec=0.1.0]
UBY 137870-000220 [spec=0.1.0] = UBY 13786999780 [spec=0.1.0]
```

The mnemonic format MUST NOT be used for formal computation.

### 7.6 Public-friendly Mnemonic Format

The public-friendly mnemonic format MAY be used for informal display.

Syntax:

```text
UBY <prefix> AD<year> [model=<model-id>] [spec=<spec-version>]
UBY <prefix> BC<year> [model=<model-id>] [spec=<spec-version>]
```

Examples:

```text
UBY 137870 AD2026 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 137870 BC221 [model=LCDM-Planck2018] [spec=0.1.0]
```

Formal data exchange SHOULD NOT rely solely on the public-friendly mnemonic format.

---

## 8. Specification Version Tag

### 8.1 Syntax

The syntax of a specification version tag is:

```text
[spec=<semver>]
```

Examples:

```text
[spec=0.1.0]
[spec=1.0.0]
[spec=1.0.0-rc.1]
```

### 8.2 Rules

1. `[spec=...]` indicates the specification version followed by the UBY expression;
2. `[spec=...]` does not indicate the cosmological model version;
3. the model version MUST be represented through `[model=...]` or the metadata field `model_version`;
4. formal data exchange and long-term archival SHOULD include `[spec=...]`;
5. if inline tags conflict with outer metadata, the inline tags SHOULD take precedence and a warning SHOULD be recorded;
6. if `[spec=...]` is missing and the context does not declare a version, a parser MUST NOT automatically assume the latest version.

---

## 9. Model Version Tag

### 9.1 Syntax

The syntax of a model version tag is:

```text
[model=<model-id>]
```

The RECOMMENDED form for `model-id` is:

```text
<family>-<source-or-release>[-<profile-or-revision>]
```

Examples:

```text
[model=LCDM-Planck2018]
[model=LCDM-WMAP9]
[model=LCDM-Planck2018-base]
[model=Custom-ArchiveA-2026]
```

### 9.2 Usage Requirements

1. Level 2 and Level 3 expressions MUST declare the model version;
2. Level 1 expressions SHOULD declare the model version, anchor, or outer metadata in formal data exchange;
3. model tags MUST be sufficient to trace parameter sources;
4. values from different model versions MUST NOT be directly compared unless a conversion relationship is documented;
5. custom models SHOULD provide parameter descriptions or references.

---

## 10. Baseline Anchor

### 10.1 Default Anchor

This specification, Working Draft 0.1.0, defines the following default anchor:

```text
Anchor ID: UBY-ANCHOR-2026-01-01Z
Source time: 2026-01-01T00:00:00Z
JD: 2461041.5
UBY: 13787002026.0
Model: LCDM-Planck2018
Spec: 0.1.0
```

Normative expression:

```text
2026-01-01T00:00:00Z
= JD 2461041.5
= UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]
```

### 10.2 Anchor Interpretation

This anchor is a conventional anchor for engineering conversion. It does not imply that the cosmic age has year-level precision.

Its construction logic is:

```text
Planck 2018 approximate current age of the universe: 13.787 Ga
13.787 Ga = 13787000000 Julian years
Astronomical year corresponding to CE 2026: 2026
Default year-level anchor: 13787000000 + 2026 = 13787002026
```

### 10.3 Anchor Changes

If a future specification or model adopts a new anchor, it MUST provide:

1. new anchor ID;
2. old anchor ID;
3. offset;
4. applicable precision level;
5. whether Level 3 is affected;
6. migration notes.

---

## 11. Conversion Algorithms

### 11.1 JD to UBY

Under the default anchor, the Level 1 conversion from JD to UBY is:

```text
UBY = (JD - 2461041.5) / 365.25 + 13787002026.0
```

### 11.2 UBY to JD

```text
JD = (UBY - 13787002026.0) × 365.25 + 2461041.5
```

### 11.3 ISO 8601 to UBY

An ISO 8601 timestamp SHOULD first be converted to JD, and then converted to UBY using the formula in Section 11.1.

Implementers SHOULD declare the time scale used, such as UTC, TAI, or TT.

### 11.4 Astronomical Year to Year-level UBY

If only year-level labeling is required, the following formula MAY be used:

```text
UBY_year = 13787000000 + astronomical_year
```

Examples:

| Native year | Astronomical year | Year-level UBY value |
| --- | ---: | ---: |
| CE 2026 | 2026 | 13787002026 |
| CE 1 | 1 | 13787000001 |
| 1 BC | 0 | 13787000000 |
| 221 BC | -220 | 13786999780 |

This formula applies only to Level 1 year-level precision contexts.

### 11.5 Redshift to UBY

Conversion from redshift to UBY MUST compute the age of the universe at redshift `z` using a cosmological model.

General form:

```text
UBY(z) = t(z)
```

where `t(z)` is the comoving time elapsed from the model origin to redshift `z`, converted to standard Julian years.

In a flat ΛCDM model, it can be expressed as:

```text
t(z) = 1/H0 × ∫[z,∞] dz' / ((1+z')E(z'))
E(z) = sqrt(Ωm(1+z)^3 + Ωr(1+z)^4 + ΩΛ)
```

Implementers SHOULD prefer validated astronomical or cosmological computation libraries and SHOULD NOT use unvalidated handwritten integration in high-precision contexts.

### 11.6 Difference Between Lookback Time and UBY

Redshift lookback time is:

```text
lookback_time(z) = t0 - t(z)
```

The UBY value is:

```text
UBY(z) = t(z)
```

The two MUST NOT be confused.

---

## 12. Rounding and Significant Digits

### 12.1 Basic Rules

1. a UBY expression MUST NOT display more significant digits than supported by the native source material;
2. Level 2 and Level 3 SHOULD be rounded according to the significant digits supported by the source and model;
3. if the original source is approximate, the UBY output SHOULD also be approximate;
4. data exchange SHOULD record the rounding rule;
5. the display format MUST NOT imply nonexistent high precision.

### 12.2 Recommended Rounding Rules

| Scenario | Recommended rule | Example |
| --- | --- | --- |
| Level 1 year-level labeling | Use integer astronomical years | CE 2026 → `UBY 13787002026 [spec=0.1.0]` |
| JD exact conversion | Preserve decimal places consistent with the input time | ISO input at second-level precision may retain fractional years |
| Geological event | Retain reasonable significant digits at ka, Ma, or Ga scale | 66.04 Ma BP |
| High-redshift event | Retain significant digits supported by the model | `UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]` |
| Approximate source | Use approximate-level output | approximately 300,000 years ago |

### 12.3 `year-floor`

`year-floor` means flooring to the year:

```text
floor(13787002026.7) = 13787002026
```

This rule is suitable for contexts that require only a year label. It MUST NOT be used for precise conversion requiring day, second, or finer granularity.

---

## 13. Data Model

### 13.1 Minimum Data Fields

When UBY data are formally stored or exchanged, the following fields SHOULD be included at minimum:

| Field | Type | Requirement | Example | Description |
| --- | --- | --- | --- | --- |
| `uby_value` | decimal/string | MUST | `13787002026.0` | Full numeric UBY value |
| `uby_version` | string | MUST | `0.1.0` | Specification version |
| `precision_level` | string | MUST | `Level 1` | Precision level |
| `source_time` | string | SHOULD | `2026-01-01T00:00:00Z` | Native time |
| `source_system` | string | SHOULD | `UTC` | Native time system |
| `model_version` | string | conditionally MUST | `LCDM-Planck2018` | Required for Level 2/3 |
| `rounding_rule` | string | SHOULD | `year-floor` | Rounding rule |
| `generated_by` | string | SHOULD | `uby-time/0.1.0` | Generating tool |

### 13.2 Anchor Fields

The following fields are RECOMMENDED:

| Field | Example |
| --- | --- |
| `anchor_id` | `UBY-ANCHOR-2026-01-01Z` |
| `anchor_jd` | `2461041.5` |
| `anchor_uby` | `13787002026.0` |
| `anchor_model` | `LCDM-Planck2018` |

### 13.3 Uncertainty Fields

The following fields are RECOMMENDED:

| Field | Example | Description |
| --- | --- | --- |
| `uncertainty_years` | `50` | Symmetric uncertainty in years |
| `interval_start_uby` | `13787001968.6` | Lower interval bound |
| `interval_end_uby` | `13787001969.4` | Upper interval bound |
| `confidence_level` | `0.95` | Confidence level |
| `uncertainty_kind` | `measurement` | Measurement, model, or combined |
| `propagation_note` | `model-dependent` | Error propagation note |

If both an interval and a symmetric uncertainty are provided, the interval SHOULD take precedence.

---

## 14. JSON Representation

### 14.1 Level 1 Example

```json
{
  "uby_value": "13787002026.0",
  "uby_version": "0.1.0",
  "precision_level": "Level 1",
  "source_time": "2026-01-01T00:00:00Z",
  "source_system": "UTC",
  "model_version": "LCDM-Planck2018",
  "anchor_id": "UBY-ANCHOR-2026-01-01Z",
  "rounding_rule": "exact-from-jd",
  "generated_by": "uby-time/0.1.0"
}
```

### 14.2 Level 3 Example

```json
{
  "uby_value": "380000",
  "uby_version": "0.1.0",
  "precision_level": "Level 3",
  "source_time": "z=1100",
  "source_system": "redshift",
  "model_version": "LCDM-Planck2018",
  "rounding_rule": "effective-digits",
  "uncertainty_kind": "model",
  "propagation_note": "requires re-computation when cosmological parameters change",
  "generated_by": "uby-time/0.1.0"
}
```

---

## 15. Conformance

### 15.1 Conformance Levels

This specification defines three conformance levels.

| Level | Name | Requirements |
| --- | --- | --- |
| C0 | Display Conformance | Correctly displays UBY expressions and retains version and model tags |
| C1 | Data Conformance | Supports full numeric values, metadata fields, precision levels, and basic validation |
| C2 | Computational Conformance | Supports normative conversion algorithms, parsing, serialization, anchors, and uncertainty handling |

### 15.2 C0: Display Conformance

A C0 implementation MUST:

1. display full numeric UBY values;
2. display `[spec=...]`;
3. display `[model=...]` for Level 2/3;
4. not remove copyright, source, or native-time descriptions;
5. not claim that UBY is absolute time.

### 15.3 C1: Data Conformance

A C1 implementation MUST satisfy C0 and additionally:

1. support the minimum data fields;
2. support JSON or an equivalent structured representation;
3. record the precision level;
4. record the native time system;
5. validate whether Level 2/3 declares a model version;
6. identify the risk of a missing specification version.

### 15.4 C2: Computational Conformance

A C2 implementation MUST satisfy C1 and additionally:

1. implement JD ↔ UBY conversion;
2. implement ISO 8601 → UBY conversion;
3. implement astronomical-year and BC-year conversion;
4. support parsing of UBY expressions;
5. support anchor metadata;
6. support uncertainty fields;
7. provide test-vector validation;
8. declare the library and parameter source used for Level 3 model computation.

---

## 16. Interoperability Requirements

### 16.1 Expression Interoperability

Different implementations that generate the same UBY expression SHOULD produce the same UBY value when the specification version, model version, anchor, input time, and rounding rule are identical.

### 16.2 Metadata Interoperability

Implementers MUST NOT exchange bare UBY values alone. Formal data exchange SHOULD exchange the following together:

1. `uby_value`;
2. `uby_version`;
3. `precision_level`;
4. `model_version`;
5. `source_time`;
6. `source_system`;
7. `rounding_rule`;
8. `anchor_id` or equivalent anchor information.

### 16.3 Parser Behavior

A parser SHOULD emit warnings for the following cases:

1. missing `[spec=...]`;
2. missing `[model=...]` for Level 2/3;
3. mnemonic prefix inconsistent with model version;
4. numeric precision obviously exceeding the source support;
5. syntactically valid but semantically incomplete expression;
6. conflict between outer metadata and inline tags.

---

## 17. Version Management

### 17.1 Version Number Format

This specification uses semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Examples:

```text
0.1.0
1.0.0
1.0.0-rc.1
```

### 17.2 Major Version

The following changes MUST increment the major version:

1. changing the definition of the UBY zero point;
2. changing the base unit;
3. changing the default anchor in a way that cannot be made compatible through metadata;
4. breaking the existing expression syntax;
5. deleting or redefining mandatory fields;
6. changing the meaning of precision levels;
7. changing core conversion algorithms.

### 17.3 Minor Version

The following changes SHOULD increment the minor version:

1. adding optional fields;
2. adding notation forms;
3. adding conformance levels;
4. adding test vectors;
5. adding model tag rules;
6. adding domain profiles.

### 17.4 Patch Version

The following changes SHOULD increment the patch version:

1. correcting documentation errors;
2. clarifying wording;
3. correcting typographical errors in examples;
4. supplementing references;
5. correcting formatting or cross-references.

### 17.5 Release Stages

| Stage | Name | Meaning |
| --- | --- | --- |
| ED | Exploratory Draft | Exploratory draft |
| WD | Working Draft | Working draft |
| PRD | Public Review Draft | Public review draft |
| RC | Release Candidate | Release candidate |
| SPEC | Specification | Formal specification |

The current version is:

```text
UBY-TLS-WD-0.1.0
```

---

## 18. Security, Misuse, and Risk

### 18.1 Legal and Engineering Risk

UBY MUST NOT be used as legal time, contract time, financial settlement time, or engineering control time.

### 18.2 Scientific Misuse Risk

UBY MUST NOT replace original scientific source data. In particular, geological, archaeological, astronomical, and cosmological data MUST retain original measurements, uncertainties, and sources.

### 18.3 Pseudo-precision Risk

Writing large-scale or highly uncertain events in high-precision decimal form is misleading. Implementers and data publishers MUST avoid pseudo-precision.

### 18.4 Model-mixing Risk

UBY values under different cosmological models may contain systematic differences. Cross-model comparison MUST declare a mapping or recompute the values.

### 18.5 Internationalization Risk

Formal machine-readable fields SHOULD prefer ASCII. Personal names, explanatory text, and presentation layers MAY use Unicode.

RECOMMENDED author credit:

```text
Han Bo
```

---

## Appendix A: ABNF Grammar

This appendix is normative.

```abnf
uby-expression    = full-numeric / magnitude / scientific / mnemonic

full-numeric      = "UBY" SP decimal [SP model-tag] [SP spec-tag]

magnitude         = "UBY" SP decimal magnitude-symbol [SP model-tag] [SP spec-tag]
magnitude-symbol  = "K" / "M" / "G" / "T"

scientific        = "UBY" SP decimal mult "10" "^" exponent [SP model-tag] [SP spec-tag]
mult              = "x" / "×"
exponent          = ["-"] 1*DIGIT

mnemonic          = academic-mnemonic / friendly-mnemonic

academic-mnemonic = "UBY" SP mnemonic-prefix sign 6DIGIT [SP model-tag] [SP spec-tag]
mnemonic-prefix   = 6DIGIT
sign              = "+" / "-"

friendly-mnemonic = "UBY" SP mnemonic-prefix SP era 1*DIGIT [SP model-tag] [SP spec-tag]
era               = "AD" / "BC"

model-tag         = "[model=" model-id "]"
model-id          = model-family "-" model-component *("-" model-component)
model-family      = 1*(ALPHA / DIGIT)
model-component   = 1*(ALPHA / DIGIT)

spec-tag          = "[spec=" spec-version "]"
spec-version      = semver [pre-release]
semver            = 1*DIGIT "." 1*DIGIT "." 1*DIGIT
pre-release       = "-" 1*(ALPHA / DIGIT / "." / "-")

decimal           = 1*DIGIT ["." 1*DIGIT]

SP                = %x20
DIGIT             = %x30-39
ALPHA             = %x41-5A / %x61-7A
```

---

## Appendix B: Example Event Table

This appendix is informative. Example values illustrate the notation and SHOULD NOT replace authoritative scientific sources.

| Event | Native description | Level | Recommended UBY expression |
| --- | --- | --- | --- |
| Big Bang model origin | Model convention | Level 3 | `UBY 0 [model=LCDM-Planck2018] [spec=0.1.0]` |
| Cosmic microwave background decoupling | Approximately 380,000 years after the Big Bang | Level 3 | `UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]` |
| Formation of the first generation of stars | Approximately 180 million years after the Big Bang | Level 3 | `UBY 180M [model=LCDM-Planck2018] [spec=0.1.0]` |
| Solar System formation | Approximately 4.567 Ga BP | Level 2 | `UBY 9.22G [model=LCDM-Planck2018] [spec=0.1.0]` |
| End-Cretaceous extinction | Approximately 66.04 Ma BP | Level 2 | `UBY 13.721G [model=LCDM-Planck2018] [spec=0.1.0]` |
| Qin Shi Huang's unification of China | 221 BC, astronomical year -220 | Level 1 | `UBY 13786999780 [spec=0.1.0]` |
| CE 1 | Astronomical year 1 | Level 1 | `UBY 13787000001 [spec=0.1.0]` |
| First human Moon landing | CE 1969 | Level 1 | `UBY 13787001969 [spec=0.1.0]` |
| Default anchor | 2026-01-01T00:00:00Z | Level 1 | `UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]` |

---

## Appendix C: Recommended Test Vectors

This appendix is normative. C2-conformant implementations SHOULD pass the following minimum tests.

| Input | Expected output |
| --- | --- |
| `2026-01-01T00:00:00Z` | `UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]` |
| `JD 2461041.5` | `UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]` |
| Astronomical year `2026` | `UBY 13787002026 [spec=0.1.0]` |
| Astronomical year `1` | `UBY 13787000001 [spec=0.1.0]` |
| Astronomical year `0` | `UBY 13787000000 [spec=0.1.0]` |
| `221 BC` | `UBY 13786999780 [spec=0.1.0]` |
| Mnemonic `UBY 137870+002026 [spec=0.1.0]` | `UBY 13787002026 [spec=0.1.0]` |
| Mnemonic `UBY 137870-000220 [spec=0.1.0]` | `UBY 13786999780 [spec=0.1.0]` |

---

## Appendix D: Reference Implementation Requirements

This appendix is informative.

An official or reference implementation SHOULD satisfy the following requirements:

1. the README front page MUST state the boundaries of UBY;
2. APIs MUST distinguish specification version, model version, and software version;
3. conversion functions MUST preserve native time sources;
4. Level 2/3 outputs MUST carry model versions;
5. JSON serialization MUST avoid floating-point precision loss;
6. CLI output SHOULD support text, JSON, and CSV;
7. minimum test vectors SHOULD be provided;
8. expression parsing and linting capabilities SHOULD be provided;
9. uncertainty fields SHOULD be provided;
10. the implementation MUST NOT claim that UBY is absolute time or a high-precision timekeeping system.

---

## Appendix E: Implementation Examples

Python example:

```python
from uby_time import iso_to_uby, format_full, format_academic_mnemonic

uby = iso_to_uby("2026-01-01T00:00:00Z")

print(format_full(uby))
print(format_academic_mnemonic(2026))
```

Expected output:

```text
UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 137870+002026 [model=LCDM-Planck2018] [spec=0.1.0]
```

CLI examples:

```bash
uby convert iso 2026-01-01T00:00:00Z
uby convert bc 221
uby parse "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]"
uby validate "UBY 137870+002026 [model=LCDM-Planck2018] [spec=0.1.0]"
```

---

## Appendix F: Future Work

This appendix is informative.

Before entering `Public Review Draft 0.9.0`, the following work is RECOMMENDED:

1. publish the English-language specification;
2. freeze the JSON Schema;
3. add more interoperability test vectors;
4. validate numeric values for example events;
5. establish a model version registry;
6. define the formal citation format;
7. separate the specification, reference implementation, and research data;
8. complete external technical review;
9. apply for a DOI;
10. publish conformance test tools.

Before entering `Specification 1.0.0`, the following items SHOULD be frozen:

1. default anchor;
2. full numeric format;
3. model tag format;
4. specification version tag format;
5. mandatory metadata fields;
6. JD ↔ UBY conversion algorithm;
7. conformance levels;
8. minimum test vectors.

---

## Appendix G: Change Log

### 0.1.0 Working Draft

| Field | Content |
| --- | --- |
| Version | 0.1.0 |
| Stage | Working Draft |
| Date | 2026-06-15 |
| Change type | Initial working draft |
| Numeric impact | Establishes the default anchor, notation, and conversion rules |
| Compatibility | Not applicable |
| Review status | Internal draft |
