"""Cross-domain proximity JOIN and null-hypothesis test utilities.

Implements the normative procedures of UBY-TLS-WD-0.1.0:

* §19 Cross-domain JOIN methodology — proximity JOIN of two record sets
  via the ``uby_value`` numeric projection track.
* §20 Null-hypothesis test for cross-domain signals — Monte Carlo
  permutation test that compares the observed alignment count against a
  randomized null model.

These utilities operate on any SQLite database that exposes the §13.2
``uby_events`` schema (``uby_value`` as a real-valued indexed column, plus
``event_category`` and ``uby_precision_level``). The
``uby_unified_timeline.sqlite`` reference dataset is one such database.
"""

from __future__ import annotations

import math
import random
import sqlite3
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class CrossDomainPair:
    """A single pair produced by §19 cross-domain proximity JOIN."""

    a_event_id: int
    b_event_id: int
    a_event_name: str
    b_event_name: str
    a_event_category: str
    b_event_category: str
    a_uby_value: float
    b_uby_value: float
    delta: float
    a_uby_precision_level: int
    b_uby_precision_level: int
    tau: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CrossDomainJoinResult:
    """Result envelope for §19 cross-domain proximity JOIN."""

    cat_a: str
    cat_b: str
    tau: float
    pairs: list[CrossDomainPair]
    null_test_result: str  # one of: not_tested, significant, not_significant

    def to_dict(self) -> dict[str, Any]:
        return {
            "cat_a": self.cat_a,
            "cat_b": self.cat_b,
            "tau": self.tau,
            "pair_count": len(self.pairs),
            "null_test_result": self.null_test_result,
            "pairs": [pair.to_dict() for pair in self.pairs],
        }


@dataclass(frozen=True)
class NullHypothesisTestResult:
    """Result envelope for §20 Monte Carlo permutation test."""

    cat_a: str
    cat_b: str
    tau: float
    n_obs: int
    null_mean: float
    null_std: float
    z_score: float
    p_value: float
    n_mc: int
    precision_level_a: int | None
    precision_level_b: int | None
    decision: str  # one of: not_significant, weak_signal, significant

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def cross_domain_join(
    db: str | Path | sqlite3.Connection,
    *,
    cat_a: str,
    cat_b: str,
    tau_years: float,
) -> CrossDomainJoinResult:
    """Execute the §19 cross-domain proximity JOIN.

    Returns all record pairs ``(a, b)`` with ``a.event_category = cat_a`` and
    ``b.event_category = cat_b`` such that ``|a.uby_value - b.uby_value| <
    tau_years``. The result is sorted by ascending ``delta``.

    The ``null_test_result`` field of the returned envelope is left as
    ``"not_tested"``; callers wishing to attach a significance verdict should
    invoke :func:`null_hypothesis_test` separately and substitute the verdict.
    """
    own_connection = isinstance(db, (str, Path))
    conn: sqlite3.Connection
    if own_connection:
        conn = sqlite3.connect(str(db))
    else:
        conn = db  # type: ignore[assignment]
    try:
        rows = conn.execute(
            """
            SELECT
                a.event_id        AS a_event_id,
                b.event_id        AS b_event_id,
                a.event_name      AS a_event_name,
                b.event_name      AS b_event_name,
                a.event_category  AS a_event_category,
                b.event_category  AS b_event_category,
                a.uby_value       AS a_uby_value,
                b.uby_value       AS b_uby_value,
                ABS(a.uby_value - b.uby_value) AS delta,
                a.uby_precision_level AS a_precision,
                b.uby_precision_level AS b_precision
            FROM uby_events a
            JOIN uby_events b
              ON a.event_category = ?
             AND b.event_category = ?
             AND ABS(a.uby_value - b.uby_value) < ?
            ORDER BY delta ASC
            """,
            (cat_a, cat_b, float(tau_years)),
        ).fetchall()
    finally:
        if own_connection:
            conn.close()

    pairs = [
        CrossDomainPair(
            a_event_id=int(r[0]),
            b_event_id=int(r[1]),
            a_event_name=r[2] or "",
            b_event_name=r[3] or "",
            a_event_category=r[4] or "",
            b_event_category=r[5] or "",
            a_uby_value=float(r[6]),
            b_uby_value=float(r[7]),
            delta=float(r[8]),
            a_uby_precision_level=int(r[9]) if r[9] is not None else 0,
            b_uby_precision_level=int(r[10]) if r[10] is not None else 0,
            tau=float(tau_years),
        )
        for r in rows
    ]
    return CrossDomainJoinResult(
        cat_a=cat_a,
        cat_b=cat_b,
        tau=float(tau_years),
        pairs=pairs,
        null_test_result="not_tested",
    )


def null_hypothesis_test(
    db: str | Path | sqlite3.Connection,
    *,
    cat_a: str,
    cat_b: str,
    tau_years: float,
    n_mc: int = 1000,
    rng: random.Random | None = None,
) -> NullHypothesisTestResult:
    """Execute the §20 Monte Carlo permutation test.

    The reference procedure (§20.2):

    1. Load ``T_a = {a.uby_value}`` and ``T_b = {b.uby_value}`` from the
       database for the two categories.
    2. Compute ``N_obs`` — the observed cross-alignment count under ``τ``.
    3. Under ``H0`` (the A/B labels are exchangeable), pool ``T_a ∪ T_b``
       and randomly reassign ``|T_a|`` values to set A and ``|T_b|`` to
       set B. Recompute the cross-alignment count ``N_mc``. This is a
       label-permutation test: it preserves the pooled temporal
       concentration while breaking the A-B distinction.
    4. For each of ``n_mc`` iterations compute ``N_mc``.
    5. Compute ``(μ, σ)`` of the null distribution.
    6. ``z = (N_obs - μ) / σ``.
    7. ``p = (1 + #{N_mc >= N_obs}) / (n_mc + 1)``.

    Returns the full result envelope required by §20.6.
    """
    if n_mc < 1:
        raise ValueError("n_mc must be >= 1")
    own_connection = isinstance(db, (str, Path))
    conn: sqlite3.Connection
    if own_connection:
        conn = sqlite3.connect(str(db))
    else:
        conn = db  # type: ignore[assignment]
    try:
        a_rows = conn.execute(
            "SELECT uby_value, uby_precision_level FROM uby_events WHERE event_category = ?",
            (cat_a,),
        ).fetchall()
        b_rows = conn.execute(
            "SELECT uby_value, uby_precision_level FROM uby_events WHERE event_category = ?",
            (cat_b,),
        ).fetchall()
    finally:
        if own_connection:
            conn.close()

    t_a = [float(r[0]) for r in a_rows if r[0] is not None]
    t_b = [float(r[0]) for r in b_rows if r[0] is not None]
    precision_a = _median_precision([r[1] for r in a_rows if r[1] is not None])
    precision_b = _median_precision([r[1] for r in b_rows if r[1] is not None])

    n_obs = _count_alignments(t_a, t_b, tau_years)

    if not t_a or not t_b:
        # Degenerate case: no records on one side — no alignment possible.
        return NullHypothesisTestResult(
            cat_a=cat_a,
            cat_b=cat_b,
            tau=float(tau_years),
            n_obs=0,
            null_mean=0.0,
            null_std=0.0,
            z_score=0.0,
            p_value=1.0,
            n_mc=int(n_mc),
            precision_level_a=precision_a,
            precision_level_b=precision_b,
            decision="not_significant",
        )

    generator = rng if rng is not None else random.Random()
    a_len = len(t_a)
    pooled = t_a + t_b
    pooled_len = len(pooled)
    n_mc_values: list[int] = []
    for _ in range(n_mc):
        # Label-permutation null (§20.2 step 3): shuffle the pooled values
        # and reassign the first |T_a| to set A and the rest to set B. This
        # preserves the pooled temporal concentration while breaking the
        # A-B distinction, producing a meaningful null distribution.
        generator.shuffle(pooled)
        permuted_a = pooled[:a_len]
        permuted_b = pooled[a_len:]
        n_mc_values.append(_count_alignments(permuted_a, permuted_b, tau_years))

    null_mean = statistics.fmean(n_mc_values)
    variance = statistics.fmean(x * x for x in n_mc_values) - null_mean * null_mean
    null_std = math.sqrt(variance) if variance > 0 else 0.0

    if null_std > 0:
        z_score = (n_obs - null_mean) / null_std
    else:
        # All Monte Carlo counts identical (e.g., τ much larger than the
        # span of the data). Treat any excess as weakly elevated.
        z_score = 0.0 if n_obs == null_mean else float("inf") if n_obs > null_mean else float("-inf")

    ge_count = sum(1 for x in n_mc_values if x >= n_obs)
    p_value = (1 + ge_count) / (n_mc + 1)

    decision = _significance_decision(z_score, p_value)

    return NullHypothesisTestResult(
        cat_a=cat_a,
        cat_b=cat_b,
        tau=float(tau_years),
        n_obs=int(n_obs),
        null_mean=float(null_mean),
        null_std=float(null_std),
        z_score=float(z_score),
        p_value=float(p_value),
        n_mc=int(n_mc),
        precision_level_a=precision_a,
        precision_level_b=precision_b,
        decision=decision,
    )


def _count_alignments(
    t_a: Sequence[float], t_b: Sequence[float], tau: float
) -> int:
    """Count ``|a - b| < τ`` pairs for the §20 test.

    Implements an O(n log n) sweep instead of the naive O(n^2) inner loop so
    that the Monte Carlo iterations stay cheap even with 10^4–10^5 records.
    """
    if not t_a or not t_b:
        return 0
    a_sorted = sorted(t_a)
    b_sorted = sorted(t_b)

    count = 0
    # Two-pointer sweep: for each a, advance b pointer past all b's that are
    # too low (b < a - tau), then count b's within [a - tau, a + tau).
    # Because a is monotonic, j is monotonic too — never reset to 0.
    j = 0
    for a in a_sorted:
        lo = a - tau
        hi = a + tau
        while j < len(b_sorted) and b_sorted[j] < lo:
            j += 1
        k = j
        while k < len(b_sorted) and b_sorted[k] < hi:
            k += 1
        count += k - j
        # Don't reset j — the next a is larger, so any b < lo for this a is
        # also < lo for the next a.
    return count


def _median_precision(values: Iterable[int]) -> int | None:
    vs = sorted(values)
    if not vs:
        return None
    n = len(vs)
    if n % 2 == 1:
        return vs[n // 2]
    return vs[n // 2 - 1]


def _significance_decision(z_score: float, p_value: float) -> str:
    """Apply the §20.3 significance decision table."""
    if z_score < 0:
        return "not_significant"
    if z_score < 2:
        return "not_significant"
    if z_score < 3:
        return "weak_signal"
    if p_value < 0.01:
        return "significant"
    return "weak_signal"


__all__ = [
    "CrossDomainPair",
    "CrossDomainJoinResult",
    "NullHypothesisTestResult",
    "cross_domain_join",
    "null_hypothesis_test",
]
