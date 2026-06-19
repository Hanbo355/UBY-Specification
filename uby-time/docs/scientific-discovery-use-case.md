# UBY Unified Timeline: A Concrete Scientific Discovery Use Case

## Selected direction

This document deepens one actionable discovery direction:

**Global mass-extinction lag analysis on a unified UBY time axis**

The goal is not merely to annotate existing datasets, but to build a reproducible cross-domain temporal database that can quantify the lag structure among:

- biological extinction events,
- biodiversity decline and recovery,
- large igneous province volcanism,
- impact events,
- geochemical excursions,
- sea-level change,
- climate proxies,
- stratigraphic boundaries.

This is one of the most realistic first high-value scientific applications for UBY because the current project has already integrated:

- ICS geologic timescale events,
- PBDB fossil occurrence records,
- a unified SQLite timeline structure,
- explicit UBY precision levels,
- explicit source provenance,
- uncertainty-aware event representation.

## Core scientific claim to test

A publishable research question can be formulated as:

> On a unified cross-domain UBY time axis, do mass-extinction intensity peaks show statistically significant and repeatable lag relationships with volcanism, impact events, carbon-cycle perturbations, and climate proxy excursions after accounting for dating uncertainty and stratigraphic boundary bias?

This question is stronger than simply asking whether two event types are “near” each other in geologic time. It asks whether UBY can produce a reproducible quantitative lag model across heterogeneous temporal systems.

## Why UBY is useful here

Traditional extinction studies often combine data expressed in different temporal forms:

| Data type | Typical time representation | Problem |
|---|---|---|
| Fossil occurrence | stratigraphic interval, early/late interval, Ma range | coarse interval uncertainty |
| Extinction boundary | named geologic boundary, GSSP, Ma estimate | boundary revisions across timescale versions |
| Volcanism | eruption pulse age, emplacement interval, Ar-Ar/U-Pb date | multi-phase interval structure |
| Impact crater | radiometric age ± uncertainty | single event with error bar |
| Isotope excursion | time-series depth-age model | model-dependent proxy chronology |
| Climate reconstruction | age model, calibrated BP, Ma, ka | model and calibration dependency |

UBY does not replace these systems. It supplies a **single sortable, queryable, uncertainty-aware index** while preserving the original representation.

This directly supports the project’s principles:

1. **Compatibility**: keep original Ma, BP, ka, stratigraphic interval, ISO, and model labels.
2. **No false precision**: do not pretend that fossil intervals are exact points.
3. **Traceability**: retain source dataset, DOI, record URI, model version, anchor version.
4. **Level-aware analysis**: compare Level 2 geologic/paleobiological events separately from Level 1 modern events.
5. **Reproducibility**: same data + same UBY profile + same anchor = same query results.

## Minimal publishable dataset design

The existing unified table is:

```sql
CREATE TABLE uby_events (
    event_id INTEGER PRIMARY KEY,
    event_name TEXT NOT NULL,
    event_category TEXT NOT NULL,
    event_subcategory TEXT,
    original_time_unit TEXT,
    original_time_value TEXT,
    original_error TEXT,
    uby_value REAL NOT NULL,
    uby_value_text TEXT NOT NULL,
    uby_model TEXT,
    uby_precision_level INTEGER NOT NULL,
    uby_precision_label TEXT,
    uby_mnemonic_iso TEXT,
    source_dataset TEXT NOT NULL,
    source_doi TEXT,
    source_record_id TEXT,
    source_record_uri TEXT,
    description TEXT,
    attribution TEXT
);
```

For the mass-extinction study, the same table can be extended by inserting additional categories:

| `event_category` | `event_subcategory` examples |
|---|---|
| `paleontology` | `fossil_occurrence`, `extinction_boundary`, `diversity_peak`, `diversity_crash` |
| `geology` | `geochronologic_boundary`, `large_igneous_province`, `volcanic_pulse`, `impact_crater` |
| `geochemistry` | `carbon_isotope_excursion`, `oxygen_isotope_excursion`, `iridium_anomaly` |
| `climate` | `warming_event`, `cooling_event`, `sea_level_fall`, `anoxia_event` |

The key point is that every event is placed on the same `uby_value` axis while preserving the original source chronology.

## Candidate authoritative datasets

A concrete first version can use public and citable datasets such as:

| Domain | Example source | UBY role |
|---|---|---|
| Geological boundaries | ICS International Chronostratigraphic Chart | fixed geologic reference frame |
| Fossil occurrence and diversity | Paleobiology Database | extinction/diversity signal |
| Large igneous provinces | Large Igneous Provinces Commission / published compilations | volcanism forcing events |
| Impact structures | Earth Impact Database | impact timing |
| Carbon isotope excursions | published δ13C compilations | carbon-cycle perturbation |
| Marine anoxia events | published OAE compilations | ocean chemistry stress |
| Sea-level curves | published Phanerozoic sea-level reconstructions | environmental forcing |

The current project already includes the first two components. The next scientific increment is to add volcanism and impact datasets.

## Event representation

### Point event

Example: an impact crater with age and uncertainty.

```json
{
  "event_name": "Chicxulub impact",
  "event_category": "geology",
  "event_subcategory": "impact_crater",
  "original_time_unit": "Ma BP",
  "original_time_value": "66.043",
  "original_error": "0.011 Ma",
  "uby_precision_level": 2,
  "source_dataset": "Earth Impact Database or cited source",
  "source_doi": "...",
  "description": "Impact event associated with the K-Pg boundary"
}
```

### Interval event

Example: a volcanic province emplacement interval.

```json
{
  "event_name": "Deccan Traps main eruptive phase",
  "event_category": "geology",
  "event_subcategory": "large_igneous_province",
  "original_time_unit": "Ma BP interval",
  "original_time_value": "66.4-65.5",
  "original_error": "source-specific",
  "uby_precision_level": 2,
  "source_dataset": "published LIP compilation",
  "source_doi": "...",
  "description": "Representative midpoint stored as uby_value; full interval retained in source fields"
}
```

### Biological signal

Example: extinction intensity peak.

```json
{
  "event_name": "End-Cretaceous marine genus extinction peak",
  "event_category": "paleontology",
  "event_subcategory": "extinction_intensity_peak",
  "original_time_unit": "Ma BP or stratigraphic bin",
  "original_time_value": "66.0",
  "original_error": "bin width or modeled confidence interval",
  "uby_precision_level": 2,
  "source_dataset": "PBDB-derived diversity curve",
  "description": "Extinction intensity peak inferred from occurrence data"
}
```

## Basic SQL analyses enabled by UBY

### 1. Find nearest forcing event before each extinction event

```sql
SELECT
    e.event_name AS extinction_event,
    e.uby_value AS extinction_uby,
    f.event_name AS forcing_event,
    f.event_subcategory AS forcing_type,
    f.uby_value AS forcing_uby,
    e.uby_value - f.uby_value AS lag_years
FROM uby_events e
JOIN uby_events f
  ON f.uby_value <= e.uby_value
WHERE e.event_subcategory IN ('extinction_boundary', 'extinction_intensity_peak')
  AND f.event_subcategory IN ('large_igneous_province', 'volcanic_pulse', 'impact_crater')
ORDER BY e.event_id, ABS(e.uby_value - f.uby_value);
```

### 2. Cross-domain window around extinction boundaries

```sql
SELECT
    event_name,
    event_category,
    event_subcategory,
    original_time_unit,
    original_time_value,
    original_error,
    uby_value,
    source_dataset,
    source_doi
FROM uby_events
WHERE uby_value BETWEEN :extinction_uby - 2000000
                    AND :extinction_uby + 2000000
ORDER BY uby_value;
```

This gives a ±2 Myr event window around a mass-extinction boundary.

### 3. Compare lead-lag distributions by forcing type

```sql
SELECT
    f.event_subcategory AS forcing_type,
    COUNT(*) AS pair_count,
    AVG(e.uby_value - f.uby_value) AS mean_lag_years,
    MIN(e.uby_value - f.uby_value) AS min_lag_years,
    MAX(e.uby_value - f.uby_value) AS max_lag_years
FROM uby_events e
JOIN uby_events f
  ON ABS(e.uby_value - f.uby_value) <= 5000000
WHERE e.event_subcategory IN ('extinction_boundary', 'extinction_intensity_peak')
  AND f.event_subcategory IN ('large_igneous_province', 'volcanic_pulse', 'impact_crater', 'carbon_isotope_excursion')
GROUP BY f.event_subcategory
ORDER BY mean_lag_years;
```

This gives a first-pass lag distribution within a ±5 Myr analysis window.

## Statistical analysis plan

A scientifically defensible workflow should include:

### 1. UBY conversion and source preservation

For every event:

- keep original source time,
- keep original uncertainty,
- compute representative `uby_value`,
- store `uby_precision_level`,
- store source dataset, DOI, URI, and model metadata.

### 2. Windowed event coincidence test

For each extinction boundary, compute the density of candidate forcing events in:

- ±0.1 Myr,
- ±0.5 Myr,
- ±1 Myr,
- ±2 Myr,
- ±5 Myr.

Then compare with randomized null models that preserve event density through geologic time.

### 3. Lag distribution test

For each forcing category:

- volcanism,
- impact,
- carbon isotope excursion,
- anoxia,
- sea-level fall,

estimate the distribution of lags relative to extinction intensity peaks.

### 4. Uncertainty-aware Monte Carlo

For each event, sample from its uncertainty interval:

- point age ± error,
- interval midpoint ± half-width,
- stratigraphic bin as uniform interval,
- model-derived time as model-dependent interval.

Repeat the lag analysis across many draws.

The output is not a single false-precision number, but a probability distribution:

```text
P(forcing precedes extinction by 0-500 kyr)
P(forcing precedes extinction by 500 kyr-1 Myr)
P(forcing overlaps extinction within uncertainty)
P(forcing follows extinction)
```

### 5. Sensitivity to timescale version

Because UBY preserves anchor and model metadata, the analysis can be repeated under different versions of the geologic timescale or calibration model.

This is essential for avoiding the common problem where apparent coincidences are artifacts of a particular timescale revision.

## Candidate original findings

The following are plausible, testable findings. They should be treated as hypotheses until the required datasets are integrated and analyzed.

### Finding A: extinction-forcing lag classes

UBY may show that mass extinctions do not share one universal lag pattern. Instead, they may cluster into distinct lag classes:

| Lag class | Possible interpretation |
|---|---|
| near-zero overlap | abrupt forcing, e.g. impact-dominated |
| 100 kyr-1 Myr lead | prolonged environmental stress before extinction peak |
| 1-5 Myr lead | long volcanic or carbon-cycle destabilization phase |
| post-extinction signal | recovery-phase volcanism, sedimentary artifact, or dating bias |

This would be valuable because it converts qualitative “coincidence” arguments into a reproducible cross-domain lag typology.

### Finding B: stratigraphic-bin bias correction

UBY may show that some previously assumed event coincidences weaken after representing fossil occurrences as intervals rather than exact dates.

This is important because many paleobiological correlations are distorted by:

- boundary rounding,
- stage-level bins,
- uneven fossil sampling,
- revised ICS ages,
- interval midpoint misuse.

UBY can explicitly retain interval width and precision level, making the bias quantifiable.

### Finding C: asymmetric lead-lag relation between volcanism and extinction

A strong result would be:

> Across Phanerozoic extinction events, volcanic pulse onsets are statistically more likely to precede extinction intensity peaks than follow them, even after uncertainty-aware Monte Carlo resampling.

This is a directly testable and publishable UBY-enabled finding.

### Finding D: impact events show sharper coincidence but lower recurrence

UBY may show that impact events have tighter temporal coincidence near specific extinction boundaries, while volcanism and geochemical perturbations show broader but more recurrent lead-lag structures.

This would clarify the difference between abrupt trigger events and long-duration environmental stressors.

## What would be genuinely original

The originality is not the individual claim that “volcanism may relate to extinction” or “impacts may relate to extinction.” Those are known debates.

The original contribution is:

> a reproducible, source-preserving, uncertainty-aware, cross-domain temporal infrastructure that lets the same lag analysis be run across all extinction boundaries and all forcing classes using one normalized UBY axis.

That is different from a narrative review or a single-boundary case study.

## Minimal next implementation step

The next code-level step should be to add a dedicated builder:

```text
examples/build_mass_extinction_lag_dataset.py
```

It should ingest:

1. current `uby_events` database,
2. a curated mass-extinction boundary table,
3. a volcanism/LIP table,
4. an impact-event table,
5. optional geochemical excursion table.

It should output:

```text
data/processed/uby_mass_extinction_lag.sqlite
data/processed/uby_mass_extinction_lag_pairs.csv
data/processed/uby_mass_extinction_lag_report.json
```

Recommended derived tables:

```sql
CREATE TABLE extinction_events AS
SELECT *
FROM uby_events
WHERE event_subcategory IN ('extinction_boundary', 'extinction_intensity_peak');

CREATE TABLE forcing_events AS
SELECT *
FROM uby_events
WHERE event_subcategory IN (
    'large_igneous_province',
    'volcanic_pulse',
    'impact_crater',
    'carbon_isotope_excursion',
    'anoxia_event',
    'sea_level_fall'
);

CREATE TABLE extinction_forcing_pairs (
    extinction_event_id INTEGER,
    forcing_event_id INTEGER,
    lag_years REAL,
    abs_lag_years REAL,
    window_years REAL,
    extinction_uncertainty_years REAL,
    forcing_uncertainty_years REAL,
    overlap_flag INTEGER,
    source_pair_key TEXT
);
```

## Minimal paper outline

A realistic first paper could be:

**Title**

> UBY-Time Enables Uncertainty-Aware Cross-Domain Lead-Lag Analysis of Phanerozoic Mass Extinctions

**Core sections**

1. Problem: geologic, paleobiologic, impact, and climate data use incompatible temporal representations.
2. Method: UBY conversion, precision levels, interval representation, provenance-preserving SQLite release.
3. Dataset: ICS + PBDB + LIP + impact + geochemical event tables.
4. Analysis: windowed coincidence, lag distributions, Monte Carlo uncertainty propagation.
5. Results: extinction-forcing lag classes and sensitivity to dating uncertainty.
6. Discussion: where coincidences are robust vs. where they are artifacts of stratigraphic binning.
7. Data release: SQLite + CSV + schema + reproducible scripts.

## Boundary of claims

The project should not initially claim:

- proof of causal relation,
- discovery of a universal extinction cycle,
- replacement of domain chronologies,
- exact dating beyond source uncertainty.

The defensible claim is:

> UBY makes cross-domain temporal hypotheses testable at database scale while preserving uncertainty, provenance, and precision level.

This is a strong enough claim for a methods/data-infrastructure paper and can later support domain-specific scientific discoveries.

## Why this is the best first direction

Among the three proposed directions, mass-extinction lag analysis is the most immediately executable because:

1. current project already has ICS and PBDB integration;
2. all relevant events are mostly Level 2, avoiding difficult Level 3 cosmological model dependency;
3. SQLite is sufficient for the expected first dataset size;
4. the scientific question is well-known but still unresolved;
5. UBY contributes a clear methodological advantage: unified, uncertainty-aware cross-domain lag analysis.

The recommended next development target is therefore:

> build a UBY mass-extinction lag-analysis dataset and use it to quantify lead-lag structures among extinction, volcanism, impact, and geochemical perturbation events.
