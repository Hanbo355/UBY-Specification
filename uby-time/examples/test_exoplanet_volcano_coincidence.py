#!/usr/bin/env python3
"""
快速统计检验：exoplanet 发现年份与 GVP 火山喷发年份"同年匹配"是否
真的超过随机预期，还是统计假象（两个数据集恰好都有大量事件落在
1990-2025 区间，必然会出现 Δ=0 的对齐）。
"""
from __future__ import annotations
import random
import sqlite3
import statistics as st


def main() -> int:
    conn = sqlite3.connect("data/processed/uby_unified_timeline.sqlite")

    # 1. 抓取 exoplanet 发现年份与 GVP 末次喷发年份（CE）
    exo = [
        int(float(r[0]))
        for r in conn.execute(
            "SELECT original_time_value FROM uby_events "
            "WHERE source_dataset LIKE 'NASA Exoplanet%' "
            "  AND original_time_unit='decimal_year'"
        )
        if r[0] and r[0].lstrip("-").replace(".", "").isdigit()
    ]
    gvp = [
        int(float(r[0]))
        for r in conn.execute(
            "SELECT original_time_value FROM uby_events "
            "WHERE source_dataset LIKE 'Smithsonian%'"
        )
        if r[0]
    ]

    print(f"Exoplanet disc years: n={len(exo)}, range=[{min(exo)},{max(exo)}]")
    print(f"GVP last-eruption years: n={len(gvp)}, range=[{min(gvp)},{max(gvp)}]")

    # 2. 观测：所有同年匹配对（笛卡尔积中 e==g 的数量）
    exo_year_set = set(exo)
    gvp_year_set = set(gvp)
    overlap_years = exo_year_set & gvp_year_set
    observed_pairs = sum(gvp.count(y) * exo.count(y) for y in overlap_years)

    print(f"\n重叠年份（同一年两边都有事件）: {len(overlap_years)} 个")
    print(f"其中近 30 年（>=1995）的重叠年份: "
          f"{sorted(y for y in overlap_years if y >= 1995)}")
    print(f"观测到的同年事件对数（observed）: {observed_pairs}")

    # 3. 蒙特卡洛零假设：保持 exo 不变，将 GVP 年份在
    #    [min(gvp), max(gvp)] 范围内均匀重采样（同样的样本量）
    #    这模拟了"GVP 喷发时间与 exoplanet 发现时间完全独立"的情形
    random.seed(42)
    n_mc = 5000
    mc_counts = []
    lo, hi = min(gvp), max(gvp)
    exo_arr = exo
    for _ in range(n_mc):
        sim_gvp = [random.randint(lo, hi) for _ in range(len(gvp))]
        # 计算与 exo 的同年匹配对数
        sim_year_set = set(sim_gvp)
        # 用 dict 加速
        sim_counts: dict[int, int] = {}
        for g in sim_gvp:
            sim_counts[g] = sim_counts.get(g, 0) + 1
        n_match = 0
        for e in exo_arr:
            if e in sim_counts:
                # 该年份在 exo 中出现次数 × 在 sim_gvp 中出现次数
                n_match += exo_arr.count(e) * sim_counts[e]
        mc_counts.append(n_match)

    mean0 = st.mean(mc_counts)
    sd0 = st.stdev(mc_counts)
    p95 = sorted(mc_counts)[int(0.95 * n_mc)]
    p99 = sorted(mc_counts)[int(0.99 * n_mc)]
    z = (observed_pairs - mean0) / sd0 if sd0 else 0

    print(f"\n蒙特卡洛零假设（n={n_mc}）:")
    print(f"  mean = {mean0:.2f}")
    print(f"  sd   = {sd0:.2f}")
    print(f"  95% 阈值 = {p95}")
    print(f"  99% 阈值 = {p99}")
    print(f"  Z = (observed - mean) / sd = {z:.3f}")
    print(f"  p < 0.05 ? {observed_pairs > p95}")
    print(f"  p < 0.01 ? {observed_pairs > p99}")

    # 4. 关键诊断：重叠年份分布
    print("\n诊断：事件年份分布")
    print(f"  Exoplanet 在 1990-2025 区间占比: "
          f"{sum(1 for y in exo if 1990 <= y <= 2025)/len(exo)*100:.1f}%")
    print(f"  GVP 末次喷发在 1990-2025 区间占比: "
          f"{sum(1 for y in gvp if 1990 <= y <= 2025)/len(gvp)*100:.1f}%")
    print("  （两者都高度集中在 1990-2025，必然产生大量 Δ=0 对齐）")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
