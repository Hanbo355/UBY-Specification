"""Tests for the §19 cross-domain JOIN helper and §20 null-hypothesis test.

These tests build an in-memory SQLite database with the §13.2 ``uby_events``
schema and exercise the two reference procedures against small synthetic
record sets where the expected alignment counts and significance decisions
can be derived by hand.
"""

from __future__ import annotations

import random
import sqlite3
from pathlib import Path
from typing import Iterable

import pytest

from uby_time import CrossDomainJoinResult, NullHypothesisTestResult
from uby_time.cli import main
from uby_time.cross_domain import (
    _count_alignments,
    cross_domain_join,
    null_hypothesis_test,
)


SCHEMA_SQL = """
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
)
"""

CREATE_INDEX_SQL = "CREATE INDEX idx_uby_value ON uby_events(uby_value)"


def _build_db(tmp_path: Path, records: Iterable[dict]) -> Path:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(SCHEMA_SQL)
    conn.execute(CREATE_INDEX_SQL)
    for r in records:
        conn.execute(
            """
            INSERT INTO uby_events (
                event_id, event_name, event_category, event_subcategory,
                original_time_unit, original_time_value, original_error,
                uby_value, uby_value_text, uby_model,
                uby_precision_level, uby_precision_label, uby_mnemonic_iso,
                source_dataset, source_doi, source_record_id,
                source_record_uri, description, attribution
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                r["event_id"], r["event_name"], r["event_category"],
                r.get("event_subcategory", ""),
                r.get("original_time_unit", ""), r.get("original_time_value", ""),
                r.get("original_error", ""),
                r["uby_value"], r.get("uby_value_text", str(r["uby_value"])),
                r.get("uby_model", "LCDM-Planck2018"),
                r.get("uby_precision_level", 1),
                r.get("uby_precision_label", "Level 1"),
                r.get("uby_mnemonic_iso", ""),
                r.get("source_dataset", "test"), r.get("source_doi", ""),
                r.get("source_record_id", ""), r.get("source_record_uri", ""),
                r.get("description", ""), r.get("attribution", ""),
            ),
        )
    conn.commit()
    conn.close()
    return db_path


# -----------------------------------------------------------------------------
# §19 cross-domain JOIN
# -----------------------------------------------------------------------------


def test_cross_domain_join_returns_pairs_within_threshold(tmp_path: Path) -> None:
    records = [
        {"event_id": 1, "event_name": "a1", "event_category": "A", "uby_value": 100.0},
        {"event_id": 2, "event_name": "a2", "event_category": "A", "uby_value": 200.0},
        {"event_id": 3, "event_name": "a3", "event_category": "A", "uby_value": 500.0},
        {"event_id": 4, "event_name": "b1", "event_category": "B", "uby_value": 101.0},
        {"event_id": 5, "event_name": "b2", "event_category": "B", "uby_value": 199.0},
        {"event_id": 6, "event_name": "b3", "event_category": "B", "uby_value": 800.0},
    ]
    db = _build_db(tmp_path, records)

    result = cross_domain_join(db, cat_a="A", cat_b="B", tau_years=2.0)

    assert isinstance(result, CrossDomainJoinResult)
    assert result.cat_a == "A"
    assert result.cat_b == "B"
    assert result.tau == 2.0
    assert result.null_test_result == "not_tested"
    deltas = [pair.delta for pair in result.pairs]
    # a1(100)↔b1(101): 1.0; a2(200)↔b2(199): 1.0; a3(500) has no B within 2.0
    assert len(result.pairs) == 2
    assert sorted(deltas) == [1.0, 1.0]
    # Sorted ascending by delta per §19
    assert result.pairs[0].delta <= result.pairs[-1].delta
    # Each pair exposes the §19.5 required fields
    pair = result.pairs[0]
    assert pair.a_event_category == "A"
    assert pair.b_event_category == "B"
    assert pair.a_uby_precision_level == 1
    assert pair.b_uby_precision_level == 1
    assert pair.tau == 2.0


def test_cross_domain_join_no_pairs_when_categories_disjoint(tmp_path: Path) -> None:
    records = [
        {"event_id": 1, "event_name": "a1", "event_category": "A", "uby_value": 100.0},
        {"event_id": 2, "event_name": "b1", "event_category": "B", "uby_value": 999.0},
    ]
    db = _build_db(tmp_path, records)

    result = cross_domain_join(db, cat_a="A", cat_b="B", tau_years=1.0)
    assert result.pairs == []


def test_cross_domain_join_to_dict_serializes_pairs(tmp_path: Path) -> None:
    records = [
        {"event_id": 1, "event_name": "a1", "event_category": "A", "uby_value": 100.0},
        {"event_id": 2, "event_name": "b1", "event_category": "B", "uby_value": 100.5},
    ]
    db = _build_db(tmp_path, records)

    result = cross_domain_join(db, cat_a="A", cat_b="B", tau_years=1.0)
    payload = result.to_dict()
    assert payload["cat_a"] == "A"
    assert payload["cat_b"] == "B"
    assert payload["tau"] == 1.0
    assert payload["pair_count"] == 1
    assert payload["null_test_result"] == "not_tested"
    assert payload["pairs"][0]["delta"] == 0.5


# -----------------------------------------------------------------------------
# §20 null-hypothesis test
# -----------------------------------------------------------------------------


def test_count_alignments_two_pointer_matches_naive() -> None:
    """Sanity check: the O(n log n) sweep must agree with the naive O(n^2)."""
    a = [0.0, 10.0, 20.0, 30.0, 40.0]
    b = [0.5, 11.0, 19.5, 35.0, 100.0]
    tau = 2.0

    naive = sum(1 for x in a for y in b if abs(x - y) < tau)
    assert naive == _count_alignments(a, b, tau)
    # Expected pairs: 0↔0.5, 10↔11, 20↔19.5, 30↔none, 40↔none
    assert naive == 3


def test_null_hypothesis_test_significant_when_clusters_align(tmp_path: Path) -> None:
    """When A and B records specifically co-locate (more than expected from
    the pooled marginal), the label-permutation null should produce fewer
    cross-alignments than observed, yielding significance.

    Design: A records sit at UBY = 0, 10, 20, ..., 490 (50 distinct points).
    B records are placed at the SAME points (genuine co-location). The
    pooled set has 100 values; under label permutation ~half land in A and
    ~half in B, so the expected cross-alignment is roughly half the
    observed (each A point also has a B point there).
    """
    records: list[dict] = []
    eid = 1
    # Set A: 50 records at UBY = 0, 10, 20, ..., 490 (spread across 490 yr)
    for i in range(50):
        records.append({
            "event_id": eid, "event_name": "a", "event_category": "A",
            "uby_value": float(i * 10),
            "uby_precision_level": 1,
        })
        eid += 1
    # Set B: 50 records at the SAME UBY points (genuine co-location)
    for i in range(50):
        records.append({
            "event_id": eid, "event_name": "b", "event_category": "B",
            "uby_value": float(i * 10),
            "uby_precision_level": 1,
        })
        eid += 1
    db = _build_db(tmp_path, records)

    result = null_hypothesis_test(
        db, cat_a="A", cat_b="B", tau_years=1.0, n_mc=500,
        rng=random.Random(123),
    )

    assert isinstance(result, NullHypothesisTestResult)
    assert result.cat_a == "A"
    assert result.cat_b == "B"
    assert result.tau == 1.0
    assert result.n_mc == 500
    # Observed: each of 50 A points has exactly 1 B within 1.0 yr → N_obs = 50.
    # Under label permutation, ~half of each point's pair lands in A and
    # ~half in B, so expected cross-alignment ≈ 50 * 0.5 = 25.
    assert result.n_obs == 50
    assert result.n_obs > result.null_mean
    assert result.z_score > 3
    assert result.p_value < 0.01
    assert result.decision == "significant"
    assert result.precision_level_a == 1
    assert result.precision_level_b == 1


def test_null_hypothesis_test_not_significant_when_independent(tmp_path: Path) -> None:
    """When A and B occupy different parts of the timeline (no specific
    co-location), the observed cross-alignment should fall within the
    label-permutation null range."""
    rng = random.Random(7)
    records: list[dict] = []
    eid = 1
    # Set A: UBY in [0, 100] — 40 records
    for _ in range(40):
        records.append({
            "event_id": eid, "event_name": "a", "event_category": "A",
            "uby_value": rng.uniform(0, 100),
            "uby_precision_level": 1,
        })
        eid += 1
    # Set B: UBY in [200, 300] — no overlap with A within τ=1.0
    for _ in range(40):
        records.append({
            "event_id": eid, "event_name": "b", "event_category": "B",
            "uby_value": rng.uniform(200, 300),
            "uby_precision_level": 1,
        })
        eid += 1
    db = _build_db(tmp_path, records)

    result = null_hypothesis_test(
        db, cat_a="A", cat_b="B", tau_years=1.0, n_mc=200,
        rng=random.Random(999),
    )

    # No A-B pairs within 1.0 yr, and permutation can't create any either
    # because the pooled set has two well-separated clusters.
    assert result.n_obs == 0
    assert result.z_score <= 0
    assert result.decision == "not_significant"


def test_null_hypothesis_test_handles_empty_categories(tmp_path: Path) -> None:
    records = [
        {"event_id": 1, "event_name": "a1", "event_category": "A", "uby_value": 100.0},
    ]
    db = _build_db(tmp_path, records)

    result = null_hypothesis_test(
        db, cat_a="A", cat_b="B", tau_years=1.0, n_mc=10,
    )
    assert result.n_obs == 0
    assert result.null_mean == 0.0
    assert result.null_std == 0.0
    assert result.z_score == 0.0
    assert result.p_value == 1.0
    assert result.decision == "not_significant"


def test_null_hypothesis_test_to_dict_includes_all_required_fields() -> None:
    """§20.6 enumerates the required outputs."""
    result = NullHypothesisTestResult(
        cat_a="A", cat_b="B", tau=1.0,
        n_obs=5, null_mean=2.0, null_std=0.5,
        z_score=6.0, p_value=0.001, n_mc=1000,
        precision_level_a=1, precision_level_b=2,
        decision="significant",
    )
    payload = result.to_dict()
    required_keys = {
        "cat_a", "cat_b", "tau", "n_obs",
        "null_mean", "null_std", "z_score", "p_value",
        "n_mc", "precision_level_a", "precision_level_b", "decision",
    }
    assert required_keys <= set(payload)


def test_null_hypothesis_test_rejects_zero_iterations(tmp_path: Path) -> None:
    records = [
        {"event_id": 1, "event_name": "a1", "event_category": "A", "uby_value": 100.0},
        {"event_id": 2, "event_name": "b1", "event_category": "B", "uby_value": 100.0},
    ]
    db = _build_db(tmp_path, records)
    with pytest.raises(ValueError):
        null_hypothesis_test(db, cat_a="A", cat_b="B", tau_years=1.0, n_mc=0)


# -----------------------------------------------------------------------------
# CLI smoke tests
# -----------------------------------------------------------------------------


def test_cli_cross_join_text(tmp_path: Path, capsys) -> None:
    records = [
        {"event_id": 1, "event_name": "a1", "event_category": "A", "uby_value": 100.0},
        {"event_id": 2, "event_name": "b1", "event_category": "B", "uby_value": 100.5},
    ]
    db = _build_db(tmp_path, records)

    rc = main([
        "cross-join",
        "--db", str(db),
        "--cat-a", "A",
        "--cat-b", "B",
        "--tau", "1.0",
        "--format", "text",
    ])
    out = capsys.readouterr().out
    assert rc == 0
    assert "cat_a=A" in out
    assert "cat_b=B" in out
    assert "pair_count=1" in out
    assert "delta=0.5" in out


def test_cli_cross_join_json(tmp_path: Path, capsys) -> None:
    records = [
        {"event_id": 1, "event_name": "a1", "event_category": "A", "uby_value": 100.0},
        {"event_id": 2, "event_name": "b1", "event_category": "B", "uby_value": 100.5},
    ]
    db = _build_db(tmp_path, records)

    rc = main([
        "cross-join",
        "--db", str(db),
        "--cat-a", "A",
        "--cat-b", "B",
        "--tau", "1.0",
        "--format", "json",
    ])
    out = capsys.readouterr().out
    assert rc == 0
    assert "\"pair_count\": 1" in out
    assert "\"null_test_result\": \"not_tested\"" in out


def test_cli_null_test_text(tmp_path: Path, capsys) -> None:
    records: list[dict] = []
    eid = 1
    # A and B co-located at UBY = 0, 5, 10, ..., 95 (20 points each)
    for i in range(20):
        records.append({
            "event_id": eid, "event_name": "a", "event_category": "A",
            "uby_value": float(i * 5),
        })
        eid += 1
    for i in range(20):
        records.append({
            "event_id": eid, "event_name": "b", "event_category": "B",
            "uby_value": float(i * 5),
        })
        eid += 1
    db = _build_db(tmp_path, records)

    rc = main([
        "null-test",
        "--db", str(db),
        "--cat-a", "A",
        "--cat-b", "B",
        "--tau", "1.0",
        "--n-mc", "100",
        "--seed", "42",
        "--format", "text",
    ])
    out = capsys.readouterr().out
    assert rc == 0
    assert "n_mc=100" in out
    assert "decision=" in out
    assert "z_score=" in out
