# Data Dictionary

This file summarizes columns for CSV datasets included in the UBY Time data release.
Types are inferred at the exchange-format level; most CSV fields are serialized as text for transparency.

## `data/processed/end_ordovician_binning_compression.csv`

- Rows: 3

| Field | Description | Unit / convention |
|---|---|---|
| `taxon_level` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `window_ma` | Age or duration field. | Ma |
| `precise_before_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `precise_after_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `precise_before_fraction` | Ratio or fraction field. | dimensionless |
| `coarse_boundary_synchronous_count` | Count field. | integer |
| `compression_ratio` | Ratio or fraction field. | dimensionless |
| `interpretation` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/end_ordovician_forcing_lags.csv`

- Rows: 2

| Field | Description | Unit / convention |
|---|---|---|
| `forcing_event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_category` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_subcategory` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_ma` | Age or duration field. | Ma |
| `forcing_uncertainty_ma` | Age or duration field. | Ma |
| `lag_years` | Year-valued time field. | years |
| `abs_lag_years` | Year-valued time field. | years |
| `overlap_flag` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/end_ordovician_sampling_bins.csv`

- Rows: 30

| Field | Description | Unit / convention |
|---|---|---|
| `bin_young_ma` | Age or duration field. | Ma |
| `bin_old_ma` | Age or duration field. | Ma |
| `bin_mid_ma` | Age or duration field. | Ma |
| `occurrence_count` | Count field. | integer |
| `unique_accepted_names` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `unique_genera` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `unique_families` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `last_accepted_names` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `last_genera` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `last_families` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/end_ordovician_sampling_control_bins.csv`

- Rows: 30

| Field | Description | Unit / convention |
|---|---|---|
| `bin_young_ma` | Age or duration field. | Ma |
| `bin_old_ma` | Age or duration field. | Ma |
| `bin_mid_ma` | Age or duration field. | Ma |
| `relation_to_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `occurrence_count` | Count field. | integer |
| `unique_accepted_names` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `unique_genera` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `unique_families` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `reference_count` | Count field. | integer |
| `formation_count` | Count field. | integer |
| `geo_cell_count` | Count field. | integer |
| `pseudo_collection_count` | Count field. | integer |
| `accepted_last_taxa` | Count field. | integer |
| `genus_last_taxa` | Count field. | integer |
| `family_last_taxa` | Count field. | integer |
| `accepted_last_per_occurrence` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `accepted_last_per_pseudo_collection` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `genus_last_per_occurrence` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `family_last_per_occurrence` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/end_ordovician_taxon_level_stability.csv`

- Rows: 3

| Field | Description | Unit / convention |
|---|---|---|
| `taxon_level` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `disappearing_taxa` | Count field. | integer |
| `before_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `after_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `before_fraction` | Ratio or fraction field. | dimensionless |
| `after_fraction` | Ratio or fraction field. | dimensionless |
| `mean_lag_years` | Year-valued time field. | years |

## `data/processed/end_ordovician_taxonomic_drivers.csv`

- Rows: 302

| Field | Description | Unit / convention |
|---|---|---|
| `grouping_level` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `group_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `disappearing_taxa` | Count field. | integer |
| `before_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `after_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `before_fraction` | Ratio or fraction field. | dimensionless |
| `after_fraction` | Ratio or fraction field. | dimensionless |
| `mean_lag_years` | Year-valued time field. | years |

## `data/processed/extinction_sensitivity_summary.csv`

- Rows: 216

| Field | Description | Unit / convention |
|---|---|---|
| `bin_size_ma` | Age or duration field. | Ma |
| `taxon_level` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `disappearance_window_ma` | Age or duration field. | Ma |
| `event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `event_ma` | Age or duration field. | Ma |
| `standing_taxa` | Count field. | integer |
| `first_appearances` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `last_appearances` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_intensity` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `disappearing_taxa` | Count field. | integer |
| `before_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `after_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `before_fraction` | Ratio or fraction field. | dimensionless |
| `after_fraction` | Ratio or fraction field. | dimensionless |
| `mean_disappearance_lag_years` | Year-valued time field. | years |
| `recovery_lag_years` | Year-valued time field. | years |
| `recovered_flag` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `nearest_forcing_event` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `nearest_forcing_category` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `nearest_forcing_subcategory` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `nearest_forcing_lag_years` | Year-valued time field. | years |
| `nearest_forcing_overlap_flag` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `end_permian_strongest_flag` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `kpg_impact_synchronous_flag` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `end_ordovician_sea_level_or_climate_flag` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

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

## `data/processed/pbdb_extinction_intensity_by_bin.csv`

- Rows: 535

| Field | Description | Unit / convention |
|---|---|---|
| `bin_id` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `bin_young_ma` | Age or duration field. | Ma |
| `bin_old_ma` | Age or duration field. | Ma |
| `bin_mid_ma` | Age or duration field. | Ma |
| `bin_mid_uby_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `standing_taxa` | Count field. | integer |
| `first_appearances` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `last_appearances` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_intensity` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `origination_intensity` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/pbdb_recovery_lag.csv`

- Rows: 6

| Field | Description | Unit / convention |
|---|---|---|
| `event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `event_ma` | Age or duration field. | Ma |
| `event_uby_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `event_uncertainty_ma` | Age or duration field. | Ma |
| `baseline_window_ma` | Age or duration field. | Ma |
| `baseline_mean_standing_taxa` | Count field. | integer |
| `recovery_threshold_fraction` | Ratio or fraction field. | dimensionless |
| `recovery_threshold_taxa` | Count field. | integer |
| `event_bin_standing_taxa` | Count field. | integer |
| `minimum_post_event_standing_taxa` | Count field. | integer |
| `recovery_bin_mid_ma` | Age or duration field. | Ma |
| `recovery_lag_years` | Year-valued time field. | years |
| `recovered_flag` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `method` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `source_doi` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/pbdb_taxon_disappearances.csv`

- Rows: 8683

| Field | Description | Unit / convention |
|---|---|---|
| `event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `event_ma` | Age or duration field. | Ma |
| `event_uncertainty_ma` | Age or duration field. | Ma |
| `disappearance_window_ma` | Age or duration field. | Ma |
| `taxon_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `taxon_rank` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `phylum` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `class_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `taxonomic_order` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `family` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `genus` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `last_ma` | Age or duration field. | Ma |
| `first_ma` | Age or duration field. | Ma |
| `duration_myr` | Ratio or fraction field. | dimensionless |
| `lag_years` | Year-valued time field. | years |
| `lag_direction` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `occurrence_count` | Count field. | integer |
| `max_uncertainty_years` | Year-valued time field. | years |
| `source_record_examples` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/pbdb_taxon_ranges.csv`

- Rows: 195194

| Field | Description | Unit / convention |
|---|---|---|
| `taxon_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `taxon_rank` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `phylum` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `class_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `taxonomic_order` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `family` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `genus` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `first_ma` | Age or duration field. | Ma |
| `last_ma` | Age or duration field. | Ma |
| `duration_myr` | Ratio or fraction field. | dimensionless |
| `max_ma_observed` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `min_ma_observed` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `max_uncertainty_years` | Year-valued time field. | years |
| `first_uby_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `last_uby_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `occurrence_count` | Count field. | integer |
| `source_record_examples` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

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

## `data/processed/uby_forcing_extinction_leadlag_pairs.csv`

- Rows: 11

| Field | Description | Unit / convention |
|---|---|---|
| `extinction_event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_ma` | Age or duration field. | Ma |
| `extinction_uby_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_uncertainty_years` | Year-valued time field. | years |
| `extinction_event_bin_standing_taxa` | Count field. | integer |
| `extinction_boundary_bin_last_appearances` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_boundary_bin_extinction_intensity` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_disappearing_taxa` | Count field. | integer |
| `extinction_disappearances_before_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_disappearances_after_boundary` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_mean_disappearance_lag_years` | Year-valued time field. | years |
| `extinction_recovery_lag_years` | Year-valued time field. | years |
| `forcing_event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_category` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_subcategory` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_ma` | Age or duration field. | Ma |
| `forcing_uby_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_uncertainty_years` | Year-valued time field. | years |
| `forcing_duration_ma` | Age or duration field. | Ma |
| `forcing_confidence_level` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_source_doi` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `lag_years` | Year-valued time field. | years |
| `abs_lag_years` | Year-valued time field. | years |
| `lag_direction` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `uncertainty_overlap_flag` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `combined_uncertainty_years` | Year-valued time field. | years |
| `window_years` | Year-valued time field. | years |
| `pair_key` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/uby_mass_extinction_lag_pairs.csv`

- Rows: 8

| Field | Description | Unit / convention |
|---|---|---|
| `extinction_event_id` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_subcategory` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_ma_bp` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_uby_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `extinction_uncertainty_years` | Year-valued time field. | years |
| `forcing_event_id` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_event_name` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_subcategory` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_ma_bp` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_uby_value` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `forcing_uncertainty_years` | Year-valued time field. | years |
| `lag_years` | Year-valued time field. | years |
| `abs_lag_years` | Year-valued time field. | years |
| `window_years` | Year-valued time field. | years |
| `overlap_flag` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `lag_direction` | Source or derived attribute; see dataset README and source script for exact derivation. | text |
| `source_pair_key` | Source or derived attribute; see dataset README and source script for exact derivation. | text |

## `data/processed/uby_unified_timeline.csv`

- Rows: 1379280

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
