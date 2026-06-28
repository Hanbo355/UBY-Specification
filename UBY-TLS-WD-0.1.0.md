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
| Release date | 2026-06-28 |
| Scope of application | Cross-scale time labeling, long-term archival, auxiliary indexing for scientific data, cross-domain data integration, and cosmological-geological-human-history narratives |
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

This document is **Working Draft 0.1.0**. It formalizes the dual-track design principle, the unified timeline data model, the cross-domain JOIN methodology, the null-hypothesis testing protocol for cross-domain signals, the quality-control framework, the provenance and audit-trail requirements, the technical validation framework, the relationship to prior work, the anchor version migration protocol, and the incremental update mechanism.

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

UBY is not designed to replace existing time systems. Instead, it provides a unified, traceable, and versioned auxiliary time label for cross-scale visualization, long-term archival, data indexing, public-science narratives, interdisciplinary data exchange, and large-scale cross-domain data integration.

A distinguishing feature of UBY is its **dual-track design**: a *semantic track* that retains all original time elements (unit, value, uncertainty, dating model, precision level), and a *numeric projection track* that projects every event onto a single real-valued axis anchored to the Big Bang. The semantic track preserves the fidelity of native time representations; the numeric projection track enables cross-domain proximity queries that are infeasible when each discipline retains only its native units.

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
7. cross-scale time labels in software systems, databases, visualizations, and APIs;
8. **large-scale cross-disciplinary data integration where proximity-based JOIN across heterogeneous time units is required**;
9. **reproducible data-mining pipelines that need a single sortable numeric axis across more than ten orders of magnitude in time**.

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
10. W3C, *RDF 1.1 Concepts and Abstract Data Model*, 2014. (Informative; referenced for comparison with ontology-based time frameworks in §24.)
11. Wilkinson, M. D., et al., *The FAIR Guiding Principles for scientific data management and stewardship*, Scientific Data, 3, 160018, 2016. (Informative; referenced for the provenance framework in §22.)

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

### 4.11 Semantic Track

The semantic track is the set of fields in a UBY record that preserve the native time representation. The semantic track fields are: `original_time_unit`, `original_time_value`, `original_error`, `uby_model`, `uby_precision_level`, `uby_precision_label`. The semantic track MUST be retained in any conformant unified timeline dataset.

### 4.12 Numeric Projection Track

The numeric projection track is the single real-valued field `uby_value` obtained by projecting a native time onto the UBY axis using the conversion algorithms of §11. The numeric projection track enables cross-domain proximity JOIN (§19) and large-scale numeric sorting.

### 4.13 Dual-track Design

The dual-track design is the UBY design principle whereby every record carries both a semantic track (§4.11) and a numeric projection track (§4.12). The two tracks are not interchangeable: the semantic track preserves fidelity; the numeric projection track enables computation. See §5.7 for the normative principle.

### 4.14 Cross-domain JOIN

A cross-domain JOIN is a database operation that retrieves records from two or more disciplines whose `uby_value` fields satisfy a proximity predicate (typically `|a.uby_value − b.uby_value| < τ`). Cross-domain JOIN is infeasible when each discipline retains only its native units.

### 4.15 Null-hypothesis Test for Cross-domain Signals

A null-hypothesis test for cross-domain signals is a statistical procedure that compares an observed cross-domain alignment against a randomized null model. The procedure is normatively defined in §20.

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

### 5.7 Dual-track Design Principle

A conformant UBY dataset that integrates more than one discipline MUST carry both tracks for every record:

1. **Semantic track** — the original native time fields (unit, value, uncertainty) plus UBY precision metadata (model, precision level, precision label). These fields preserve the fidelity of the source. They MUST NOT be derived from or overwritten by the numeric projection track.
2. **Numeric projection track** — a single real-valued `uby_value` field obtained by applying the conversion algorithms of §11 to the semantic track. This field is the *only* field used for cross-domain proximity JOIN (§19), sorting, and numeric comparison across disciplines.

The dual-track design is **not** a redundant pair of representations: each track serves a distinct, non-substitutable role. Removing the semantic track destroys fidelity (an event's `uby_value` of `135715499995.6` cannot be inverted to recover `±0.4 Ma` uncertainty or `stratigraphic` dating method); removing the numeric projection track destroys cross-domain joinability.

Implementations MAY additionally expose the dual tracks as a layered API: the semantic track as a structured object, the numeric projection track as a scalar index column. Both layers MUST be backed by the same underlying record.

A dataset that carries only `uby_value` and discards the native fields is **non-conformant** with this specification from version 0.1.0 onward.

### 5.8 Cross-domain Falsifiability Principle

Any claim of a cross-domain temporal signal derived from UBY alignment MUST be accompanied by a null-hypothesis test as specified in §20. Observed alignments that fail the null-hypothesis test MUST be reported as non-significant and MUST NOT be described as discoveries.

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

This specification, Working Draft 0.1.0, defines the default anchor as follows:

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

If a future specification or model adopts a new anchor, it MUST follow the migration protocol in §25.

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

### 11.5 BCE/CE to UBY

For a traditional BC year `n` (where 1 BC is the year immediately before CE 1):

```text
astronomical_year = 1 - n
UBY_year = 13787000000 + (1 - n)
```

Example: 221 BC → astronomical year -220 → `UBY 13786999780 [spec=0.1.0]`.

### 11.6 BP / ka BP / Ma BP / Ga BP to UBY

For a value `t_bp` expressed in years before present, where "present" is defined as the anchor year (2026 by default):

```text
UBY = 13787002026.0 - t_bp_years
```

where `t_bp_years` is the BP value converted to Julian years. For `ka BP`, multiply by 1000; for `Ma BP`, by 10^6; for `Ga BP`, by 10^9.

### 11.7 Redshift to UBY (Level 3)

For a redshift `z`, the corresponding UBY is computed from the cosmological comoving age at `z`:

```text
UBY(z) = age_of_universe_at_z=0 - age_of_universe_at_z
       = t0 - t(z)
```

where `t(z)` is the comoving age at redshift `z` obtained from the cosmological model. The model version MUST be declared. UBY values computed from different cosmological models MUST NOT be directly compared.

### 11.8 Decimal Calendar Year to UBY

For a decimal calendar year `y` (e.g., 2026.5):

```text
UBY = 13787002026.0 + (y - 2026.0)
```

---

## 12. Rounding and Significant Digits

### 12.1 Rounding Rule

The default rounding rule is year-floor for Level 1 and significant-digit rounding for Level 2/3.

### 12.2 Significant Digits

The number of significant digits in a UBY value MUST NOT exceed that supported by the source material. A value derived from a source with ±0.4 Ma uncertainty MUST NOT carry more than 7 significant digits.

### 12.3 Display vs Storage

Stored `uby_value` SHOULD preserve the full numeric precision of the conversion. Display formats (§7.2–7.6) MAY truncate or round for readability.

---

## 13. Data Model

### 13.1 Minimal UBY Record

A minimal UBY record carries the numeric projection track and the minimum metadata for traceability:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `uby_value` | REAL | MUST | Numeric projection track: years since the conventional zero point |
| `model_version` | TEXT | MUST (L2/L3) | Cosmological model identifier |
| `spec_version` | TEXT | SHOULD | Specification version, e.g. `0.1.0` |
| `anchor_id` | TEXT | SHOULD | Anchor identifier used for conversion |

### 13.2 Conformant Unified Timeline Event (Dual-track)

A conformant unified timeline dataset that integrates more than one discipline MUST carry, for every record, the full dual-track schema:

| Field | Type | Track | Required | Description |
| --- | --- | --- | --- | --- |
| `event_id` | INTEGER | — | MUST | Stable unique identifier within the dataset |
| `event_name` | TEXT | — | MUST | Human-readable event label |
| `event_category` | TEXT | — | MUST | Top-level discipline, e.g. `cosmology`, `geology`, `paleontology`, `paleoclimate`, `astronomy`, `paleoecology`, `instrumental`, `spaceflight` |
| `event_subcategory` | TEXT | — | SHOULD | Fine-grained category, e.g. `model_origin`, `reference_milestone`, `eruption`, `occurrence` |
| `original_time_unit` | TEXT | semantic | MUST | Native unit, e.g. `Ma BP`, `yr BP`, `decimal_year`, `redshift`, `BCE`, `JD` |
| `original_time_value` | TEXT | semantic | MUST | Native value, preserved as text to avoid float precision loss |
| `original_error` | TEXT | semantic | SHOULD | Native uncertainty, e.g. `±0.4 Ma`, `±5 yr` |
| `uby_value` | REAL | numeric | MUST | Numeric projection onto the UBY axis |
| `uby_value_text` | TEXT | numeric | SHOULD | Canonical UBY expression string, e.g. `UBY 13.721G [model=LCDM-Planck2018] [spec=0.1.0]` |
| `uby_model` | TEXT | semantic | MUST (L2/L3) | Conversion model, e.g. `LCDM-Planck2018` |
| `uby_precision_level` | INTEGER | semantic | MUST | Precision level 1/2/3 per §6 |
| `uby_precision_label` | TEXT | semantic | SHOULD | Human-readable precision label |
| `uby_mnemonic_iso` | TEXT | numeric | MAY | Academic mnemonic per §7.5 |
| `source_dataset` | TEXT | provenance | MUST | Source dataset name |
| `source_doi` | TEXT | provenance | SHOULD | DOI of the source dataset |
| `source_record_id` | TEXT | provenance | MUST | Stable identifier within the source dataset |
| `source_record_uri` | TEXT | provenance | SHOULD | Resolvable URI of the source record |
| `description` | TEXT | — | MAY | Free-text description |
| `attribution` | TEXT | provenance | SHOULD | Attribution string per the source license |

### 13.3 Field Roles

- **Semantic track fields** (`original_time_unit`, `original_time_value`, `original_error`, `uby_model`, `uby_precision_level`, `uby_precision_label`) preserve native fidelity and MUST be sourced directly from the original record. They MUST NOT be derived from `uby_value`.
- **Numeric projection track fields** (`uby_value`, `uby_value_text`, `uby_mnemonic_iso`) are derived from the semantic track via §11 algorithms and are used for sorting, indexing, and cross-domain JOIN.
- **Provenance fields** (`source_dataset`, `source_doi`, `source_record_id`, `source_record_uri`, `attribution`) support the audit trail (§22).

### 13.4 Storage Format

A conformant dataset MAY be stored in any of:

- SQLite (RECOMMENDED for medium-scale datasets, up to ~10^7 records);
- Parquet (RECOMMENDED for larger datasets);
- CSV with a sidecar JSON Schema (acceptable for exchange only).

In all cases, the `uby_value` column MUST be indexed for range queries.

### 13.5 Conformance Levels for Datasets

| Level | Name | Requirement |
| --- | --- | --- |
| **C0** | Minimal | Carries `uby_value` + `model_version` only. Acceptable for single-discipline datasets. |
| **C1** | Provenance | C0 + provenance fields. Acceptable for archival. |
| **C2** | Dual-track conformant | Full schema of §13.2. REQUIRED for any cross-disciplinary unified timeline dataset claiming conformance to this specification from 0.1.0 onward. |

---

## 14. JSON Representation

### 14.1 Minimal JSON

```json
{
  "uby_value": 13787002026.0,
  "model": "LCDM-Planck2018",
  "spec": "0.1.0"
}
```

### 14.2 Conformant Dual-track JSON

```json
{
  "event_id": 1,
  "event_name": "End-Cretaceous extinction",
  "event_category": "paleontology",
  "original_time_unit": "Ma BP",
  "original_time_value": "66.04",
  "original_error": "±0.04 Ma",
  "uby_value": 13786999780.0,
  "uby_value_text": "UBY 13.721G [model=LCDM-Planck2018] [spec=0.1.0]",
  "uby_model": "LCDM-Planck2018",
  "uby_precision_level": 2,
  "uby_precision_label": "cross-scale proportional narrative",
  "source_dataset": "PBDB",
  "source_doi": "10.5281/zenodo.XXXXXXX",
  "source_record_id": "occ:XXXXX",
  "source_record_uri": "https://paleobiodb.org/classic/basic/occasion_single?id=XXXXX",
  "attribution": "Creative Commons CC-BY 4.0"
}
```

---

## 15. Conformance

### 15.1 Conformance Targets

This specification defines three conformance targets:

1. **UBY expression parser** — a software component that parses UBY expressions conforming to §7 and Appendix A.
2. **UBY converter** — a software component that converts native time to UBY and back, conforming to §11.
3. **UBY unified timeline dataset** — a dataset that integrates two or more disciplines and conforms to §13.

### 15.2 Conformance Levels

| Level | Name | Applicable to | Requirement |
| --- | --- | --- | --- |
| **C0** | Minimal | parsers, converters, single-discipline datasets | Parses/converts per §7 and §11 |
| **C1** | Provenance | converters, datasets | C0 + provenance fields per §22 |
| **C2** | Dual-track | cross-disciplinary datasets | C1 + full dual-track schema per §13.2 |

A cross-disciplinary unified timeline dataset that claims conformance to UBY-TLS 0.1.0 MUST meet C2.

---

## 16. Interoperability Requirements

### 16.1 With ISO 8601

Implementations MUST support bidirectional conversion between ISO 8601 timestamps and UBY via JD (§11.1, §11.3).

### 16.2 With Julian Date

Implementations MUST support bidirectional conversion between JD and UBY (§11.1, §11.2).

### 16.3 With Geological Time Scales

Implementations SHOULD support conversion from ICS chronostratigraphic ages to UBY via the `Ma BP` / `Ga BP` algorithm (§11.6).

### 16.4 With Cosmological Redshift

Implementations SHOULD support conversion from redshift `z` to UBY using a declared cosmological model (§11.7).

### 16.5 With BP Notation

Implementations MUST support conversion from `yr BP` / `ka BP` / `Ma BP` / `Ga BP` to UBY (§11.6), where "present" is the anchor year (2026 by default).

### 16.6 With Database Systems

A conformant dataset stored in a relational database MUST expose `uby_value` as a real-valued indexed column. Cross-domain JOIN (§19) MUST be expressible as a single SQL statement without per-record unit conversion in the query.

---

## 17. Version Management

### 17.1 Specification Version

The specification version follows Semantic Versioning 2.0.0:

- MAJOR: incompatible changes to the conversion algorithms, anchor, or conformance schema;
- MINOR: backward-compatible additions (e.g., new sections, new optional fields);
- PATCH: backward-compatible corrections and clarifications.

### 17.2 Model Version

The model version is independent of the specification version. Multiple model versions MAY coexist under a single specification version.

### 17.3 Implementation Version

The implementation (software) version is independent of both the specification and model versions.

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

### 18.6 Cross-domain Spurious Correlation Risk

Cross-domain proximity JOIN (§19) can produce alignments that are statistically expected rather than physically meaningful. Any cross-domain alignment reported as a signal MUST be accompanied by a null-hypothesis test (§20). Implementations and publications MUST NOT report cross-domain alignments as discoveries without such a test.

---

## 19. Cross-domain JOIN Methodology

### 19.1 Motivation

When two disciplines use incompatible time units (e.g., `Ma BP` in paleontology and `decimal_year` in astronomy), proximity JOIN between their records is infeasible without a unifying axis. The UBY numeric projection track provides such an axis.

### 19.2 Definition

A **cross-domain proximity JOIN** between two record sets A and B is the set of pairs `(a, b)` such that:

```text
|a.uby_value - b.uby_value| < τ
```

where `τ` is the proximity threshold in Julian years.

### 19.3 Reference SQL

The reference SQL form is:

```sql
SELECT a.event_name, b.event_name, ABS(a.uby_value - b.uby_value) AS delta
FROM uby_events a
JOIN uby_events b
  ON a.event_category = :cat_a
 AND b.event_category = :cat_b
 AND ABS(a.uby_value - b.uby_value) < :tau
ORDER BY delta;
```

### 19.4 Threshold Selection

The threshold `τ` SHOULD be chosen with reference to the coarser of the two precision levels:

- Level 1 × Level 1: `τ` in the order of years;
- Level 1 × Level 2: `τ` in the order of 10^5 years;
- Level 2 × Level 2: `τ` in the order of 10^5–10^6 years;
- Level 3 × any: comparison requires explicit model declaration and `τ` in the order of 10^6 years or larger.

Implementations SHOULD record the chosen `τ` and the precision levels of both sides in the result metadata.

### 19.5 Required Output Fields

Every cross-domain JOIN result set MUST include:

- `a.event_name`, `b.event_name`;
- `a.uby_value`, `b.uby_value`;
- `delta = ABS(a.uby_value - b.uby_value)`;
- `a.event_category`, `b.event_category`;
- `a.uby_precision_level`, `b.uby_precision_level`;
- `tau` (the threshold used);
- `null_test_result` (per §20): one of `not_tested`, `significant`, `not_significant`.

### 19.6 Limitations

Cross-domain JOIN establishes **temporal proximity**, not **causal relation**. A pair `(a, b)` satisfying the proximity predicate does not imply that `a` caused `b`, or that the two events share a physical mechanism. Any causal claim requires independent physical evidence.

---

## 20. Null-hypothesis Testing for Cross-domain Signals

### 20.1 Motivation

Cross-domain proximity JOINs will, in general, produce non-zero alignment counts even when the two record sets are statistically independent. This is because both sets often concentrate in the same temporal window (e.g., both the modern astronomical record and the modern volcanic record concentrate in 1990–2025). A null-hypothesis test is required to distinguish signal from sampling bias.

### 20.2 Reference Procedure

The reference null-hypothesis test is a **Monte Carlo label-permutation test** with the following protocol:

1. Let `T_a = {a_i.uby_value}` and `T_b = {b_j.uby_value}` be the UBY value sets of the two record sets.
2. Let `N_obs = |{(i, j) : |a_i - b_j| < τ}|` be the observed cross-alignment count.
3. Under the null hypothesis `H0` that the A/B labels are exchangeable, pool the combined set `T = T_a ∪ T_b` and randomly reassign `|T_a|` values to set A and `|T_b|` values to set B. This preserves the pooled temporal concentration while breaking the A-B distinction.

   > **Rationale.** A bootstrap that resamples `T_b` from its own empirical distribution is degenerate for the alignment-count statistic: `E[N_mc] = N_obs` by linearity, so the z-score is identically zero and the test can never reject. The label-permutation null avoids this degeneracy because it redistributes the pooled values across the two sets, producing a meaningful null distribution whose mean is strictly less than `N_obs` whenever genuine co-location exists.

4. For each of `M` Monte Carlo iterations (RECOMMENDED `M ≥ 1000`), compute the cross-alignment count `N_mc`.
5. Compute the null distribution mean `μ` and standard deviation `σ` of `N_mc`.
6. Compute the z-score: `z = (N_obs - μ) / σ`.
7. Compute the empirical p-value: `p = (1 + |{m : N_mc[m] >= N_obs}|) / (M + 1)`.

### 20.3 Significance Decision

| Condition | Decision |
| --- | --- |
| `z < 0` | Observed alignment is **below random expectation**. NOT significant. |
| `0 <= z < 2` | Observed alignment is **within random expectation**. NOT significant. |
| `2 <= z < 3` | **Weak signal**. Report with caution; multiple-testing correction required. |
| `z >= 3` AND `p < 0.01` | **Significant signal**. May be reported as a candidate discovery, subject to physical-mechanism validation. |

### 20.4 Multiple-testing Correction

If the same dataset is tested against `K` different cross-domain partners, a Bonferroni or Benjamini-Hochberg correction MUST be applied to the per-test significance threshold.

### 20.5 Physical-mechanism Validation

A statistically significant cross-domain alignment MUST NOT be reported as a scientific discovery without an independent, documented physical mechanism that plausibly links the two event classes. Statistical significance is necessary but not sufficient.

### 20.6 Reference Implementation

A reference implementation of this test MUST expose:

- the observed alignment count `N_obs`;
- the null distribution `(μ, σ)`;
- the z-score;
- the empirical p-value;
- the Monte Carlo iteration count `M`;
- the chosen threshold `τ`;
- the precision levels of both record sets.

---

## 21. Quality-control Framework

### 21.1 Scope

This section defines the minimum quality-control (QC) requirements for a conformant UBY unified timeline dataset.

### 21.2 Physical-bound Filters

Each `event_category` SHOULD declare a physical upper and lower bound on `uby_value`. Records outside these bounds MUST be either filtered out or flagged with a `qc_flag` field.

| Category | Lower bound (UBY) | Upper bound (UBY) | Rationale |
| --- | --- | --- | --- |
| cosmology | 0 | 13,787,002,026 | Cannot predate Big Bang or postdate present |
| astronomy (stellar age) | 0 | 13,787,002,026 | Stellar age cannot exceed cosmic age |
| geology | 9,200,000,000 | 13,787,002,026 | Solar System formation to present |
| paleontology | 12,870,000,000 | 13,787,002,026 | Phanerozoic to present |
| instrumental | 13,786,999,026 | 13,787,002,026 | ~1000 yr CE to present |

### 21.3 Outlier Detection

Records whose `uby_value` violates the physical bound MUST be quarantined. A quarantine log MUST record:

- `event_id`;
- `original_time_value`;
- computed `uby_value`;
- the bound violated;
- the action taken (`dropped`, `flagged`, `corrected`).

### 21.4 Completeness Audit

A conformant dataset MUST report:

- total record count per `event_category`;
- count of records missing each semantic-track field;
- count of records missing each provenance field;
- count of records flagged by physical-bound filters.

### 21.5 Reproducibility Audit

A conformant dataset MUST ship with a `metadata.json` sidecar that records:

- the UBY specification version;
- the model version;
- the anchor identifier;
- the build timestamp (UTC);
- the source dataset list with per-source record counts;
- the QC summary per §21.4;
- the software version that produced the dataset.

---

## 22. Provenance and Audit Trail

### 22.1 Per-record Provenance

Every record in a conformant unified timeline dataset MUST carry:

- `source_dataset`: the name of the originating dataset;
- `source_record_id`: a stable identifier that uniquely identifies the record within the source dataset;
- `source_doi` (SHOULD): the DOI of the source dataset;
- `source_record_uri` (SHOULD): a resolvable URI of the source record;
- `attribution` (SHOULD): the attribution string required by the source license.

### 22.2 Dataset-level Provenance

A conformant dataset MUST ship with a `PROVENANCE.md` (or equivalent machine-readable) document that records:

- every source dataset's name, version, release date, DOI, license;
- the transformation pipeline used to produce the unified dataset;
- the software version(s) used;
- the build timestamp;
- the QC summary per §21.

### 22.3 FAIR Alignment

A conformant dataset SHOULD align with the FAIR principles:

- **Findable**: persistent identifiers (DOI) for the dataset and its sources;
- **Accessible**: open access via a recognized repository (Zenodo, Figshare, Dryad);
- **Interoperable**: the dual-track schema of §13.2 enables cross-disciplinary JOIN;
- **Reusable**: per-source licenses and attributions are preserved per record.

### 22.4 Audit Log

For datasets intended for long-term archival, an audit log SHOULD be maintained that records every rebuild, every QC filter action, and every anchor migration (per §25).

---

## 23. Technical Validation Framework

### 23.1 Scope

This section defines the minimum technical validation that a conformant UBY dataset MUST undergo and document.

### 23.2 Conversion Validation

For each conversion path (§11.1–11.8), a test suite MUST verify:

- the round-trip identity: `convert_back(convert_forward(x)) ≈ x` within the declared precision;
- the minimum test vectors of Appendix C;
- the model-dependence declaration for Level 3 paths.

### 23.3 Cross-domain JOIN Validation

A conformant dataset MUST include at least one worked example of a cross-domain JOIN (§19), together with the null-hypothesis test result (§20). The example MUST be reproducible from the published dataset and code.

### 23.4 Sampling-bias Validation

For any cross-domain signal reported as significant (§20.3), the validation MUST include:

- a check that the signal is not an artifact of shared temporal concentration (e.g., both record sets concentrated in 1990–2025);
- a sensitivity analysis on the threshold `τ`;
- a multiple-testing correction if more than one cross-domain partner was tested.

### 23.5 Rebuild Reproducibility

Two independent rebuilds of the dataset from the same sources and software version MUST produce byte-identical `uby_value` fields (allowing for floating-point representation differences of less than 1 ULP).

---

## 24. Relationship to Prior Work

### 24.1 Cosmic Calendar (Sagan, 1977)

The Cosmic Calendar maps the cosmic history onto a single calendar year for popular-science visualization. UBY shares the conceptual choice of the Big Bang as the zero point, but differs in three respects:

1. UBY is a queryable numeric axis, not a visualization metaphor;
2. UBY carries the dual-track schema (§13) preserving native time fields;
3. UBY defines a formal conversion specification (§11) and conformance levels (§15).

### 24.2 Unified Time Framework (UTF, Wang et al., 2022)

The Unified Time Framework proposes an ontology-based time framework for the geosciences, with six time elements (time type, expression, reference, unit, uncertainty, dating method) organized as RDF/OWL nodes queried via SPARQL. UBY and UTF adopt **complementary design philosophies**:

| Dimension | UTF | UBY |
| --- | --- | --- |
| Design philosophy | Ontology-based; preserves semantic diversity | Dual-track; preserves semantic diversity **and** adds a numeric projection |
| Data model | RDF triples + 6-element ontology | Relational; semantic-track columns + single `uby_value` column |
| Query language | SPARQL | SQL |
| Numeric projection | Not provided | Provided (`uby_value`) |
| Cross-domain JOIN | Not supported directly | Supported (§19) |
| Null-hypothesis testing | Not provided | Provided (§20) |
| Published dataset | Not released | Reference implementation ships a C2-conformant unified timeline dataset |
| Discipline coverage | Geosciences (geology, geography, paleontology) | Cosmology, astronomy, geology, paleontology, paleoclimate, paleoecology, volcanology, instrumental, spaceflight |
| Temporal span | Phanerozoic + human history (~5×10^8 yr) | 17 orders of magnitude (Big Bang to present) |

UBY does **not** claim conceptual novelty over UTF for the idea of unifying time across disciplines. UBY's contributions relative to UTF are:

1. instantiating the unified-time concept as a 1.5M+-record cross-disciplinary database;
2. anchoring the time axis to a physical reference (Big Bang = 0) rather than an abstract root node;
3. adding the numeric projection track and the cross-domain JOIN methodology (§19);
4. adding the null-hypothesis testing protocol for cross-domain signals (§20).

### 24.3 Universal Space-Time Referencing System (USTRS)

USTRS proposes a universal space-time encoding for navigation and deep-space applications. UBY shares the choice of a cosmological origin but differs in scope: USTRS targets space-time positioning for navigation, while UBY targets cross-disciplinary data integration. The two are not directly comparable.

### 24.4 ISO 8601, JD, ICS

UBY is a supplementary layer that interoperates with these established systems per §16. It does not replace them.

### 24.5 Positioning Statement

UBY is best understood as a **physical-coordinate complement** to ontology-based time frameworks such as UTF: it preserves the semantic fidelity that UTF provides, while adding a numeric projection that enables cross-domain proximity queries at scale. UBY is suitable for large-scale cross-disciplinary data integration and proximity-based data mining; UTF remains suitable for knowledge-graph construction and semantic reasoning.

---

## 25. Anchor Version Migration Protocol

### 25.1 When Migration Is Required

Anchor migration is required when:

1. the cosmological model parameters change (e.g., Planck 2018 → Planck 2025);
2. the anchor reference epoch changes (e.g., 2026-01-01 → 2030-01-01);
3. the Julian-year definition is revised (unlikely; would be a MAJOR version change).

### 25.2 Migration Record

A migration MUST be recorded with the following fields:

| Field | Description |
| --- | --- |
| `migration_id` | Unique identifier for the migration |
| `old_anchor_id` | Identifier of the previous anchor |
| `new_anchor_id` | Identifier of the new anchor |
| `old_uby_value` | Sample UBY value under the old anchor |
| `new_uby_value` | Sample UBY value under the new anchor |
| `offset` | `new_uby_value - old_uby_value` (a constant for all records) |
| `affected_precision_levels` | Subset of {1, 2, 3} |
| `migration_date` | UTC timestamp |
| `migration_software_version` | Software version that performed the migration |
| `migration_notes` | Free-text notes |

### 25.3 Migration Procedure

1. Freeze the old dataset and archive it.
2. Compute the constant offset between the old and new anchors.
3. For every record, set `new_uby_value = old_uby_value + offset`.
4. Update `uby_value_text` and `uby_mnemonic_iso` per §7.
5. Update `anchor_id`, `model_version`, and `spec_version` fields.
6. Run the QC checks of §21 on the migrated dataset.
7. Publish the migration record per §25.2.

### 25.4 Compatibility

If only the anchor reference epoch changes (e.g., 2026 → 2030), Level 1 records are affected by a constant offset; Level 2/3 records may or may not be affected depending on whether the model parameters also change. The migration record MUST declare which precision levels are affected.

### 25.5 Backward Compatibility

Datasets built under an older anchor remain valid for archival use, but cross-dataset JOINs between records built under different anchors MUST NOT be performed without migration. Implementations SHOULD detect anchor mismatches via the `anchor_id` field and refuse the JOIN or trigger migration.

---

## 26. Incremental Update Mechanism

### 26.1 When Incremental Update Is Permitted

Incremental update (appending new records without rebuilding the entire dataset) is permitted when:

1. the anchor has not changed (per §25);
2. the model version has not changed;
3. the new records conform to the same schema (§13.2);
4. the new records have been QC-checked per §21.

### 26.2 Update Procedure

1. Validate new records against the schema (§13.2) and QC bounds (§21.2).
2. Append new records with monotonically increasing `event_id`.
3. Update the dataset's `metadata.json` with:
   - the new total record count;
   - the new source dataset list (if a new source was added);
   - the update timestamp;
   - the software version that performed the update.
4. Re-run the cross-domain JOIN validation (§23.3) on a sample to confirm no regressions.

### 26.3 When Full Rebuild Is Required

A full rebuild is REQUIRED when:

- the anchor changes (per §25);
- the model version changes;
- the specification version introduces an incompatible schema change;
- a QC filter is retroactively applied to existing records.

### 26.4 Versioning of Incremental Updates

Each incremental update SHOULD be assigned a build identifier of the form `<dataset-version>+<update-sequence>`, e.g., `v0.1.0+001`. The build identifier MUST be recorded in `metadata.json`.

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
| `66.04 Ma BP` | `UBY 13786999780 [spec=0.1.0]` (Level 2; precision floor) |
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
10. the implementation MUST NOT claim that UBY is absolute time or a high-precision timekeeping system;
11. **a C2-conformant unified timeline dataset SHOULD ship with a `metadata.json` sidecar per §21.5 and a `PROVENANCE.md` per §22.2**;
12. **the implementation SHOULD provide a cross-domain JOIN helper and a null-hypothesis test utility per §19 and §20**.

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

Cross-domain JOIN example (per §19):

```python
from uby_time.cross_domain import cross_domain_join, null_hypothesis_test

result = cross_domain_join(
    db="uby_unified_timeline.sqlite",
    cat_a="astronomy",
    cat_b="geology",
    tau_years=1.0,
)
test = null_hypothesis_test(
    db="uby_unified_timeline.sqlite",
    cat_a="astronomy",
    cat_b="geology",
    tau_years=1.0,
    n_mc=1000,
)
print(result, test)
```

CLI examples:

```bash
uby convert iso 2026-01-01T00:00:00Z
uby convert bc 221
uby parse "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]"
uby validate "UBY 137870+002026 [model=LCDM-Planck2018] [spec=0.1.0]"
uby cross-join --cat-a astronomy --cat-b geology --tau 1.0
uby null-test --cat-a astronomy --cat-b geology --tau 1.0 --n-mc 1000
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
10. publish conformance test tools;
11. **publish a reference implementation of the cross-domain JOIN helper (§19) and the null-hypothesis test utility (§20)**;
12. **publish a worked example of an anchor migration (§25) with a real offset**;
13. **collect at least one third-party usage report**.

Before entering `Specification 1.0.0`, the following items SHOULD be frozen:

1. default anchor;
2. full numeric format;
3. model tag format;
4. specification version tag format;
5. mandatory metadata fields;
6. JD ↔ UBY conversion algorithm;
7. conformance levels;
8. minimum test vectors;
9. **the dual-track schema of §13.2**;
10. **the cross-domain JOIN output schema of §19.5**;
11. **the null-hypothesis test output schema of §20.6**.

---

## Appendix G: Change Log

### 0.1.0 Working Draft

| Field | Content |
| --- | --- |
| Version | 0.1.0 |
| Stage | Working Draft |
| Date | 2026-06-28 |
| Change type | Initial working draft |
| Numeric impact | Establishes the default anchor, notation, and conversion rules |
| Summary of changes | Establishes the default anchor (UBY-ANCHOR-2026-01-01Z), notation, and conversion algorithms (§11, including §11.5–11.8). Defines the dual-track design principle (§5.7), cross-domain falsifiability principle (§5.8), the full unified timeline event schema with C0/C1/C2 conformance levels (§13), cross-domain spurious-correlation risk (§18.6), cross-domain JOIN methodology (§19), null-hypothesis testing protocol (§20), quality-control framework (§21), provenance and audit trail (§22), technical validation framework (§23), relationship to prior work (§24: UTF, Cosmic Calendar, USTRS), anchor version migration protocol (§25), and incremental update mechanism (§26). Includes §16.6 database interoperability. Includes appendices A–G. |