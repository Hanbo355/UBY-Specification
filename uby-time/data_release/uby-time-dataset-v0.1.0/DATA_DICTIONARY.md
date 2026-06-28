# Data Dictionary

This file summarizes columns for CSV datasets included in the UBY Time data release.
Types are inferred at the exchange-format level; most CSV fields are serialized as text for transparency.

## `data/processed/external_databases_uby.csv`

- Rows: 14567

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_subcategory` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_unit` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `measured_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `measured_value_unit` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uncertainty_years` | Half-width or propagated time uncertainty. | years |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `description` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/external_records_uby.csv`

- Rows: 12169

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_subcategory` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_unit` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `measured_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `measured_value_unit` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uncertainty_years` | Half-width or propagated time uncertainty. | years |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `description` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/ics_chart_uby.csv`

- Rows: 122

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_type` | Event category. | controlled text |
| `original_time_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_unit` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `source_system` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `years_before_present` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uncertainty_years` | Half-width or propagated time uncertainty. | years |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_expression` | Human-readable full UBY expression. | UBY syntax |
| `uby_magnitude_expression` | Compact magnitude-style UBY expression. | UBY syntax |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_jd` | Julian Day of anchor. | JD |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `rounding_rule` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `generated_by` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `validation_messages` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/nasa_exoplanet_archive_uby.csv`

- Rows: 1169

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_type` | Event category. | controlled text |
| `planet_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `hostname` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `discovery_year` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `representative_astronomical_year` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uncertainty_years` | Half-width or propagated time uncertainty. | years |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_expression` | Human-readable full UBY expression. | UBY syntax |
| `uby_magnitude_expression` | Compact magnitude-style UBY expression. | UBY syntax |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_jd` | Julian Day of anchor. | JD |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `rounding_rule` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `generated_by` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `discovery_method` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `discovery_facility` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `system_planet_count` | Count field. | integer |
| `orbital_period_days` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `planet_radius_earth` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `planet_mass_earth` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `stellar_effective_temperature_k` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `stellar_radius_solar` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `stellar_mass_solar` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `right_ascension_deg` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `declination_deg` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `validation_messages` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/nasa_jpl_cneos_fireballs_uby.csv`

- Rows: 1064

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_type` | Event category. | controlled text |
| `source_time_utc` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_expression` | Human-readable full UBY expression. | UBY syntax |
| `uby_magnitude_expression` | Compact magnitude-style UBY expression. | UBY syntax |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_jd` | Julian Day of anchor. | JD |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `rounding_rule` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `generated_by` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `energy_kt` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `impact_energy_kt` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `latitude` | Modern latitude when available. | decimal degrees |
| `longitude` | Modern longitude when available. | decimal degrees |
| `altitude_km` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `velocity_km_s` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `validation_messages` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/pbdb_animalia_phanerozoic_uby.csv`

- Rows: 1348072

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_type` | Event category. | controlled text |
| `accepted_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `identified_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `identified_rank` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `accepted_rank` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `early_interval` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `late_interval` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `max_ma` | Older bound of geological age interval. | Ma BP |
| `min_ma` | Younger bound of geological age interval. | Ma BP |
| `representative_ma_midpoint` | Midpoint of geological age interval. | Ma BP |
| `years_before_present_midpoint` | Midpoint expressed as years before present. | years BP |
| `uncertainty_years` | Half-width or propagated time uncertainty. | years |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_expression` | Human-readable full UBY expression. | UBY syntax |
| `uby_magnitude_expression` | Compact magnitude-style UBY expression. | UBY syntax |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_jd` | Julian Day of anchor. | JD |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `rounding_rule` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `generated_by` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `longitude` | Modern longitude when available. | decimal degrees |
| `latitude` | Modern latitude when available. | decimal degrees |
| `phylum` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `class_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `taxonomic_order` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `family` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `genus` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `formation` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `geological_group` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `member` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `reference_no` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `validation_messages` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/pbdb_collections_animalia_phanerozoic_uby.csv`

- Rows: 180000

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_type` | Event category. | controlled text |
| `collection_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `collection_no` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `n_occs` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `early_interval` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `late_interval` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `max_ma` | Older bound of geological age interval. | Ma BP |
| `min_ma` | Younger bound of geological age interval. | Ma BP |
| `representative_ma_midpoint` | Midpoint of geological age interval. | Ma BP |
| `years_before_present_midpoint` | Midpoint expressed as years before present. | years BP |
| `uncertainty_years` | Half-width or propagated time uncertainty. | years |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_expression` | Human-readable full UBY expression. | UBY syntax |
| `uby_magnitude_expression` | Compact magnitude-style UBY expression. | UBY syntax |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_jd` | Julian Day of anchor. | JD |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `rounding_rule` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `generated_by` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `longitude` | Modern longitude when available. | decimal degrees |
| `latitude` | Modern latitude when available. | decimal degrees |
| `paleolongitude` | Paleogeographic longitude when available. | decimal degrees |
| `paleolatitude` | Paleogeographic latitude when available. | decimal degrees |
| `country` | Count field. | integer |
| `state` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `county` | Count field. | integer |
| `formation` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `geological_group` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `member` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `environment` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `lithology1` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `lithology2` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `lithification1` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `lithification2` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `collection_type` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `collection_methods` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `research_group` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `reference_no` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `primary_reference` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `validation_messages` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/pbdb_dinosauria_uby.csv`

- Rows: 94

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_type` | Event category. | controlled text |
| `accepted_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `identified_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `identified_rank` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `accepted_rank` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `early_interval` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `late_interval` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `max_ma` | Older bound of geological age interval. | Ma BP |
| `min_ma` | Younger bound of geological age interval. | Ma BP |
| `representative_ma_midpoint` | Midpoint of geological age interval. | Ma BP |
| `years_before_present_midpoint` | Midpoint expressed as years before present. | years BP |
| `uncertainty_years` | Half-width or propagated time uncertainty. | years |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_expression` | Human-readable full UBY expression. | UBY syntax |
| `uby_magnitude_expression` | Compact magnitude-style UBY expression. | UBY syntax |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_jd` | Julian Day of anchor. | JD |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `rounding_rule` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `generated_by` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `longitude` | Modern longitude when available. | decimal degrees |
| `latitude` | Modern latitude when available. | decimal degrees |
| `phylum` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `class_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `taxonomic_order` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `family` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `genus` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `formation` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `geological_group` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `member` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `reference_no` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `validation_messages` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/simbad_high_redshift_objects_uby.csv`

- Rows: 5000

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_type` | Event category. | controlled text |
| `object_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `object_type` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `right_ascension_deg` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `declination_deg` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `redshift` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_unit` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uncertainty_years` | Half-width or propagated time uncertainty. | years |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_value_text` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_jd` | Julian Day of anchor. | JD |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `rounding_rule` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `generated_by` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `propagation_note` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/uby_forcing_events.csv`

- Rows: 24

| Field | Description | Unit / convention |
|---|---|---|
| `event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_category` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_subcategory` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `ma_bp` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uncertainty_ma` | Age or duration field. | Ma |
| `duration_ma` | Age or duration field. | Ma |
| `source_compilation` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `source_doi` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `evidence_type` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `confidence_level` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `notes` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_unit` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_value_float` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_model` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_precision_level` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_precision_label` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uncertainty_years` | Half-width or propagated time uncertainty. | years |
| `generated_by` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_version` | UBY specification/software version. | semantic version |

## `data/processed/uby_unified_timeline.csv`

- Rows: 1586016

| Field | Description | Unit / convention |
|---|---|---|
| `event_id` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `event_category` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `event_subcategory` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_unit` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_time_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `original_error` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_value_text` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_model` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_precision_level` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_precision_label` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uby_mnemonic_iso` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `source_dataset` | Source dataset or API. | text |
| `source_doi` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `description` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/usgs_earthquakes_uby_benchmark.csv`

- Rows: 23756

| Field | Description | Unit / convention |
|---|---|---|
| `source_dataset` | Source dataset or API. | text |
| `source_record_id` | Source record identifier. | text |
| `source_record_uri` | Source record URI if available. | URI |
| `event_label` | Human-readable event label. | text |
| `event_type` | Event category. | controlled text |
| `source_time_utc` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `precision_level` | UBY precision level assigned by source time type. | Level 1/2/3 |
| `uby_value` | Representative UBY numeric label derived from source time. | UBY years |
| `uby_expression` | Human-readable full UBY expression. | UBY syntax |
| `uby_magnitude_expression` | Compact magnitude-style UBY expression. | UBY syntax |
| `model_version` | Model or convention used for UBY conversion. | text |
| `uby_version` | UBY specification/software version. | semantic version |
| `anchor_id` | UBY anchor identifier. | text |
| `anchor_jd` | Julian Day of anchor. | JD |
| `anchor_uby` | UBY value of anchor. | UBY years |
| `rounding_rule` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `generated_by` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `latitude` | Modern latitude when available. | decimal degrees |
| `longitude` | Modern longitude when available. | decimal degrees |
| `depth_km` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `magnitude` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `magnitude_type` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `place` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `usgs_type` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `status` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `location_source` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `magnitude_source` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `updated_time_utc` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `validation_messages` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `attribution` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
