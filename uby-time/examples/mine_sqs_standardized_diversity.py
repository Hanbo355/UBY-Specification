"""Sampling-standardized Phanerozoic diversity via SQS (coverage-based subsampling).

This directly addresses the single biggest weakness flagged in the raw
range-through diversity analysis: the "Pull of the Recent" sampling artifact.
Raw occurrence counts make recent bins look hyper-diverse simply because recent
rocks are sampled far more intensively.

Method: Shareholder Quorum Subsampling (Alroy 2010), implemented here as the
modern coverage-based rarefaction (Chao & Jost 2012, Hsieh et al. iNEXT logic):

  For each 1-Myr bin:
    1. Tally genus occurrence frequencies n_i; N = sum(n_i).
    2. Estimate sample coverage with the Chao (2012) estimator:
         u1 = f1 (singletons), u2 = f2 (doubletons)
         C_hat = 1 - (f1/N) * ((N-1)*f1 / ((N-1)*f1 + 2*f2))
       (falls back to Good's u = 1 - f1/N when f2 == 0).
    3. If C_hat < quorum, the bin cannot support the quorum -> NA.
    4. Otherwise subsample WITHOUT replacement, drawing genera in a
       frequency-weighted random order (Efraimidis-Spirakis keys) and
       accumulating each genus's frequency share f_i until the accumulated
       coverage reaches the quorum; the number of genera drawn is the
       quorum-standardized richness for that trial.
    5. Repeat for `trials` and take the mean.

We then compare the SQS curve to the raw range-through curve to show whether
the recent diversity peak is real or a sampling artifact, and we re-examine
whether the major extinction-rate peaks survive standardization.

Data source: real PBDB occurrence-level export (genus, representative_ma).
Research status: sampling_standardized_first_pass (SQS diversity only).
Extinction-rate standardization would additionally require Alroy's three-timer
/ gap-filler estimators, noted in claim_boundary.
"""

from __future__ import annotations

import csv
import json
import math
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

PHANEROZOIC_BASE_MA = 538.8
BIN_MA = 1.0
QUORUM = 0.6
TRIALS = 50
MIN_OCCURRENCES = 20  # a bin needs at least this many occurrences to attempt SQS
RANDOM_SEED = 20260621

# Canonical boundaries for cross-checking only (not used to bias anything).
CANONICAL_BOUNDARIES_MA = {
    "End-Ordovician": 443.8,
    "Late Devonian": 372.0,
    "End-Permian": 251.9,
    "End-Triassic": 201.4,
    "End-Cretaceous": 66.0,
}


def find_occurrence_file() -> Path:
    here = Path(__file__).resolve().parent.parent
    candidate = here / "data" / "processed" / "pbdb_animalia_phanerozoic_uby.csv"
    if not candidate.exists():
        raise FileNotFoundError(f"Expected PBDB occurrences at {candidate}")
    return candidate


def bin_index(ma: float) -> int:
    """Map a Ma value to an integer bin index (older = larger). bin i covers (i, i+1] Ma."""
    return int(math.floor(ma))


def stream_bin_counts(path: Path):
    """Stream the 1 GB occurrence file, accumulating bin -> {genus: count}."""
    bin_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total = 0
    used = 0
    skipped = 0
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            total += 1
            genus = (row.get("genus") or "").strip()
            ma_raw = (row.get("representative_ma_midpoint") or "").strip()
            if not genus or not ma_raw:
                skipped += 1
                continue
            try:
                ma = float(ma_raw)
            except ValueError:
                skipped += 1
                continue
            if ma <= 0 or ma > PHANEROZOIC_BASE_MA:
                skipped += 1
                continue
            b = bin_index(ma)
            bin_counts[b][genus] += 1
            used += 1
    return bin_counts, total, used, skipped


def chao_coverage(freqs: list[int], n: int) -> float:
    """Chao (2012) sample coverage estimator; fall back to Good's u when f2 == 0."""
    f1 = sum(1 for c in freqs if c == 1)
    f2 = sum(1 for c in freqs if c == 2)
    if n == 0:
        return 0.0
    if f2 > 0:
        return 1.0 - (f1 / n) * (((n - 1) * f1) / ((n - 1) * f1 + 2 * f2))
    return 1.0 - f1 / n


def sqs_richness(counts: dict[str, int], quorum: float, trials: int, rng: random.Random):
    """Coverage-based (SQS) standardized richness for one bin.

    Returns (mean_richness, coverage, n_occurrences, raw_richness) or None if
    coverage is insufficient for the quorum.
    """
    genera = list(counts.keys())
    freqs = [counts[g] for g in genera]
    n = sum(freqs)
    raw_richness = len(genera)
    if n < MIN_OCCURRENCES:
        return None
    coverage = chao_coverage(freqs, n)
    if coverage < quorum:
        return None
    # frequency share of each genus
    shares = [c / n for c in freqs]
    richness_samples = []
    for _ in range(trials):
        # Efraimidis-Spirakis weighted random order (without replacement):
        # key_i = u_i ** (1 / w_i); larger key drawn first.
        keyed = sorted(
            range(len(genera)),
            key=lambda i: rng.random() ** (1.0 / shares[i]),
            reverse=True,
        )
        cum = 0.0
        drawn = 0
        for idx in keyed:
            cum += shares[idx]
            drawn += 1
            if cum >= quorum:
                break
        richness_samples.append(drawn)
    mean_rich = sum(richness_samples) / len(richness_samples)
    return mean_rich, coverage, n, raw_richness


def main() -> int:
    t0 = time.perf_counter()
    rng = random.Random(RANDOM_SEED)
    path = find_occurrence_file()
    print(f"[1/4] Streaming occurrences from {path.name} (~1 GB) ...", flush=True)
    bin_counts, total, used, skipped = stream_bin_counts(path)
    print(f"      rows total={total}, used={used}, skipped={skipped}, "
          f"bins_with_data={len(bin_counts)}", flush=True)

    print(f"[2/4] Running SQS (quorum={QUORUM}, trials={TRIALS}) per bin ...", flush=True)
    curve = []  # (bin_old_ma, raw_richness, sqs_richness, coverage, n_occ)
    for b in sorted(bin_counts.keys(), reverse=True):
        counts = bin_counts[b]
        res = sqs_richness(counts, QUORUM, TRIALS, rng)
        bin_old_ma = b + 1  # bin covers (b, b+1] Ma; report older edge
        if res is None:
            raw = len(counts)
            n = sum(counts.values())
            cov = chao_coverage(list(counts.values()), n)
            curve.append({
                "bin_old_ma": bin_old_ma,
                "raw_richness": raw,
                "sqs_richness": None,
                "coverage": round(cov, 4),
                "n_occurrences": n,
                "status": "below_quorum_or_too_few",
            })
        else:
            mean_rich, cov, n, raw = res
            curve.append({
                "bin_old_ma": bin_old_ma,
                "raw_richness": raw,
                "sqs_richness": round(mean_rich, 2),
                "coverage": round(cov, 4),
                "n_occurrences": n,
                "status": "ok",
            })

    # [3/4] Compare Pull-of-the-Recent: raw vs SQS peak location.
    print("[3/4] Comparing raw vs SQS diversity peaks ...", flush=True)
    ok_bins = [c for c in curve if c["sqs_richness"] is not None]
    raw_peak = max(curve, key=lambda c: c["raw_richness"])
    sqs_peak = max(ok_bins, key=lambda c: c["sqs_richness"]) if ok_bins else None

    # Recent (Cenozoic, < 66 Ma) vs deep-time mean to quantify Pull of the Recent.
    def mean_of(field, predicate):
        vals = [c[field] for c in ok_bins if predicate(c) and c[field] is not None]
        return sum(vals) / len(vals) if vals else None

    raw_recent = mean_of("raw_richness", lambda c: c["bin_old_ma"] <= 66)
    raw_deep = mean_of("raw_richness", lambda c: c["bin_old_ma"] > 66)
    sqs_recent = mean_of("sqs_richness", lambda c: c["bin_old_ma"] <= 66)
    sqs_deep = mean_of("sqs_richness", lambda c: c["bin_old_ma"] > 66)

    raw_recent_ratio = (raw_recent / raw_deep) if (raw_recent and raw_deep) else None
    sqs_recent_ratio = (sqs_recent / sqs_deep) if (sqs_recent and sqs_deep) else None

    # [4/4] SQS-based diversity drops near canonical boundaries.
    print("[4/4] Checking SQS diversity drops at canonical boundaries ...", flush=True)
    sqs_by_ma = {c["bin_old_ma"]: c["sqs_richness"] for c in ok_bins}
    boundary_checks = {}
    for name, b_ma in CANONICAL_BOUNDARIES_MA.items():
        before = None
        after = None
        center = round(b_ma)
        # diversity just BEFORE (older, larger Ma) and AFTER (younger, smaller Ma)
        # the boundary. Start at dma=1 so we never read the boundary bin itself
        # for both sides (which would force before == after, drop == 0).
        for dma in range(1, 9):
            if before is None and (center + dma) in sqs_by_ma:
                before = sqs_by_ma[center + dma]
            if after is None and (center - dma) in sqs_by_ma:
                after = sqs_by_ma[center - dma]
        drop = None
        if before and after and before > 0:
            drop = round((before - after) / before, 4)
        boundary_checks[name] = {
            "boundary_ma": b_ma,
            "sqs_richness_before": before,
            "sqs_richness_after": after,
            "fractional_drop": drop,
            "drop_detected": bool(drop is not None and drop > 0.1),
        }
    drops_detected = sum(1 for v in boundary_checks.values() if v["drop_detected"])

    elapsed = time.perf_counter() - t0

    report = {
        "database": "UBY SQS sampling-standardized Phanerozoic diversity",
        "description": (
            "Coverage-based (Chao-Jost) Shareholder Quorum Subsampling of real "
            "PBDB genus occurrences on the UBY axis, to remove the Pull-of-the-"
            "Recent sampling artifact and test whether diversity structure and "
            "extinction-related drops survive standardization."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "inputs": {"pbdb_occurrences_csv": str(path)},
        "parameters": {
            "bin_ma": BIN_MA,
            "quorum": QUORUM,
            "trials": TRIALS,
            "min_occurrences_per_bin": MIN_OCCURRENCES,
            "coverage_estimator": "Chao 2012 (fallback Good's u when f2==0)",
            "subsampling": "coverage-based rarefaction, weighted without replacement (Efraimidis-Spirakis)",
            "random_seed": RANDOM_SEED,
        },
        "counts": {
            "rows_total": total,
            "rows_used": used,
            "rows_skipped": skipped,
            "bins_with_data": len(bin_counts),
            "bins_passing_quorum": len(ok_bins),
        },
        "pull_of_the_recent_test": {
            "raw_diversity_peak": {
                "bin_old_ma": raw_peak["bin_old_ma"],
                "raw_richness": raw_peak["raw_richness"],
            },
            "sqs_diversity_peak": (
                {
                    "bin_old_ma": sqs_peak["bin_old_ma"],
                    "sqs_richness": sqs_peak["sqs_richness"],
                }
                if sqs_peak else None
            ),
            "raw_mean_recent_cenozoic": round(raw_recent, 2) if raw_recent else None,
            "raw_mean_deeptime": round(raw_deep, 2) if raw_deep else None,
            "raw_recent_to_deeptime_ratio": round(raw_recent_ratio, 3) if raw_recent_ratio else None,
            "sqs_mean_recent_cenozoic": round(sqs_recent, 2) if sqs_recent else None,
            "sqs_mean_deeptime": round(sqs_deep, 2) if sqs_deep else None,
            "sqs_recent_to_deeptime_ratio": round(sqs_recent_ratio, 3) if sqs_recent_ratio else None,
            "interpretation": (
                "If the raw recent/deep ratio is large but the SQS ratio is much "
                "smaller, the recent diversity peak was largely a Pull-of-the-Recent "
                "sampling artifact."
            ),
        },
        "boundary_diversity_drops_sqs": boundary_checks,
        "boundary_drops_detected": f"{drops_detected}/{len(CANONICAL_BOUNDARIES_MA)}",
        "research_status": "sampling_standardized_first_pass",
        "claim_boundary": [
            "SQS standardizes DIVERSITY; extinction-RATE standardization would additionally require Alroy three-timer / gap-filler estimators.",
            "Quorum 0.6 and 1-Myr bins are pragmatic choices; results should be checked across quorum levels and stage-level bins.",
            "Coverage estimation is sensitive to singletons; very low-sample bins are correctly dropped rather than reported.",
            "This is a faithful first-pass SQS, not a full divDyn/iNEXT production pipeline.",
        ],
        "build_performance": {
            "wall_seconds": elapsed,
            "rows_per_second": used / elapsed if elapsed > 0 else None,
        },
    }

    out_dir = path.parent
    report_path = out_dir / "phanerozoic_sqs_diversity_report.json"
    curve_path = out_dir / "phanerozoic_sqs_diversity_curve.csv"

    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    with curve_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["bin_old_ma", "raw_richness", "sqs_richness", "coverage", "n_occurrences", "status"])
        for c in curve:
            w.writerow([c["bin_old_ma"], c["raw_richness"], c["sqs_richness"],
                        c["coverage"], c["n_occurrences"], c["status"]])

    # Console summary.
    print("\n=== SQS SAMPLING-STANDARDIZED DIVERSITY SUMMARY ===")
    print(f"Rows used: {used} | bins passing quorum {QUORUM}: {len(ok_bins)}/{len(bin_counts)}")
    print(f"RAW peak:  {raw_peak['raw_richness']} genera at {raw_peak['bin_old_ma']} Ma")
    if sqs_peak:
        print(f"SQS peak:  {sqs_peak['sqs_richness']} genera at {sqs_peak['bin_old_ma']} Ma")
    print("\n-- Pull of the Recent --")
    print(f"RAW recent/deep diversity ratio: {report['pull_of_the_recent_test']['raw_recent_to_deeptime_ratio']}")
    print(f"SQS recent/deep diversity ratio: {report['pull_of_the_recent_test']['sqs_recent_to_deeptime_ratio']}")
    print("\n-- SQS diversity drops at canonical boundaries --")
    for name, c in boundary_checks.items():
        flag = "DROP" if c["drop_detected"] else "----"
        print(f"  [{flag}] {name} ({c['boundary_ma']} Ma): "
              f"before={c['sqs_richness_before']} after={c['sqs_richness_after']} "
              f"drop={c['fractional_drop']}")
    print(f"\nBoundary diversity drops detected: {drops_detected}/{len(CANONICAL_BOUNDARIES_MA)}")
    print(f"Wall time: {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
