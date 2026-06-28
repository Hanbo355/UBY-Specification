import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable


PROCESSED_DIR = Path("data/processed")
UNIFIED_DB = PROCESSED_DIR / "uby_unified_timeline.sqlite"

UBY_EVENT_COLUMNS = [
    "event_name",
    "event_category",
    "event_subcategory",
    "original_time_unit",
    "original_time_value",
    "original_error",
    "uby_value",
    "uby_value_text",
    "uby_model",
    "uby_precision_level",
    "uby_precision_label",
    "uby_mnemonic_iso",
    "source_dataset",
    "source_doi",
    "source_record_id",
    "source_record_uri",
    "description",
    "attribution",
]


def table_exists(cursor: sqlite3.Cursor, table_name: str, schema: str = "main") -> bool:
    cursor.execute(
        f"""
        SELECT 1
        FROM {schema}.sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def get_count(cursor: sqlite3.Cursor, table_name: str, schema: str = "main") -> int:
    cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
    return int(cursor.fetchone()[0])


def attach_database(cursor: sqlite3.Cursor, db_path: Path, alias: str) -> bool:
    if not db_path.exists():
        print(f"  跳过: 源数据库不存在: {db_path}")
        return False
    cursor.execute(f"ATTACH DATABASE ? AS {alias}", (str(db_path),))
    return True


def detach_database(cursor: sqlite3.Cursor, alias: str) -> None:
    try:
        cursor.execute(f"DETACH DATABASE {alias}")
    except sqlite3.OperationalError as exc:
        # SQLite may keep an attached read-only source locked until the
        # surrounding write transaction is committed. The connection close at
        # the end of the merge releases any remaining attachments, so this
        # should not interrupt an otherwise successful merge.
        if "locked" in str(exc).lower():
            print(f"  提示: {alias} 将在连接关闭时自动释放 ({exc})")
            return
        raise


def insert_select(
    cursor: sqlite3.Cursor,
    select_sql: str,
    source_label: str,
) -> int:
    before = cursor.connection.total_changes
    columns = ", ".join(UBY_EVENT_COLUMNS)
    cursor.execute(
        f"""
        INSERT INTO main.uby_events ({columns})
        {select_sql}
        """
    )
    inserted = cursor.connection.total_changes - before
    print(f"  成功新增 {inserted:,} 条记录: {source_label}")
    return int(inserted)


def merge_pbdb_collections(cursor: sqlite3.Cursor) -> tuple[str, int, int]:
    """合并 PBDB collection API 数据集。"""
    source_db = PROCESSED_DIR / "pbdb_collections_animalia_phanerozoic_uby.sqlite"
    alias = "src_pbdb_collections"
    table = "pbdb_collections_animalia_phanerozoic_uby"
    label = "PBDB Collections Animalia Phanerozoic"

    print("\n1. 合并 PBDB Collections 数据集...")
    if not attach_database(cursor, source_db, alias):
        return label, 0, 0

    try:
        if not table_exists(cursor, table, alias):
            print(f"  跳过: 源表不存在: {table}")
            return label, 0, 0

        source_count = get_count(cursor, table, alias)
        inserted = insert_select(
            cursor,
            f"""
            SELECT
                s.event_label AS event_name,
                'paleontology' AS event_category,
                s.event_type AS event_subcategory,
                'Ma BP' AS original_time_unit,
                CASE
                    WHEN s.max_ma IS NOT NULL AND s.min_ma IS NOT NULL
                        THEN CAST(s.max_ma AS TEXT) || '-' || CAST(s.min_ma AS TEXT)
                    ELSE CAST(s.representative_ma_midpoint AS TEXT)
                END AS original_time_value,
                CAST(s.uncertainty_years AS TEXT) AS original_error,
                CAST(s.uby_value AS REAL) AS uby_value,
                s.uby_expression AS uby_value_text,
                s.model_version AS uby_model,
                CASE
                    WHEN CAST(s.precision_level AS TEXT) LIKE '%1%' THEN 1
                    WHEN CAST(s.precision_level AS TEXT) LIKE '%2%' THEN 2
                    WHEN CAST(s.precision_level AS TEXT) LIKE '%3%' THEN 3
                    ELSE NULL
                END AS uby_precision_level,
                s.precision_level AS uby_precision_label,
                NULL AS uby_mnemonic_iso,
                s.source_dataset AS source_dataset,
                NULL AS source_doi,
                CAST(s.source_record_id AS TEXT) AS source_record_id,
                s.source_record_uri AS source_record_uri,
                'PBDB collection'
                    || CASE WHEN s.collection_name IS NOT NULL THEN ': ' || s.collection_name ELSE '' END
                    || CASE WHEN s.country IS NOT NULL THEN '; country=' || s.country ELSE '' END
                    || CASE WHEN s.formation IS NOT NULL THEN '; formation=' || s.formation ELSE '' END
                    || CASE WHEN s.environment IS NOT NULL THEN '; environment=' || s.environment ELSE '' END
                    || CASE WHEN s.n_occs IS NOT NULL THEN '; occurrences=' || CAST(s.n_occs AS TEXT) ELSE '' END
                    AS description,
                s.attribution AS attribution
            FROM {alias}.{table} AS s
            WHERE NOT EXISTS (
                SELECT 1
                FROM main.uby_events AS u
                WHERE u.source_dataset = s.source_dataset
                  AND u.source_record_id = CAST(s.source_record_id AS TEXT)
                  AND u.event_name = s.event_label
            )
            """,
            label,
        )
        return label, source_count, inserted
    finally:
        detach_database(cursor, alias)


def merge_uby_forcing_events(cursor: sqlite3.Cursor) -> tuple[str, int, int]:
    """合并 UBY forcing event compilation 数据集。"""
    source_db = PROCESSED_DIR / "uby_forcing_events.sqlite"
    alias = "src_uby_forcing"
    table = "forcing_events"
    label = "UBY Forcing Events"

    print("\n2. 合并 UBY Forcing Events 数据集...")
    if not attach_database(cursor, source_db, alias):
        return label, 0, 0

    try:
        if not table_exists(cursor, table, alias):
            print(f"  跳过: 源表不存在: {table}")
            return label, 0, 0

        source_count = get_count(cursor, table, alias)
        inserted = insert_select(
            cursor,
            f"""
            SELECT
                s.event_name AS event_name,
                'forcing' AS event_category,
                s.forcing_subcategory AS event_subcategory,
                COALESCE(s.original_time_unit, 'Ma BP') AS original_time_unit,
                CAST(s.ma_bp AS TEXT) AS original_time_value,
                CAST(s.uncertainty_ma AS TEXT) AS original_error,
                CAST(s.uby_value AS REAL) AS uby_value,
                'UBY ' || CAST(s.uby_value AS TEXT)
                    || ' [model=' || COALESCE(s.uby_model, 'unspecified') || '] [spec=0.1.0]'
                    AS uby_value_text,
                s.uby_model AS uby_model,
                s.uby_precision_level AS uby_precision_level,
                s.uby_precision_label AS uby_precision_label,
                NULL AS uby_mnemonic_iso,
                s.source_compilation AS source_dataset,
                s.source_doi AS source_doi,
                s.source_record_id AS source_record_id,
                s.source_record_uri AS source_record_uri,
                'Forcing category=' || COALESCE(s.forcing_category, '')
                    || '; evidence=' || COALESCE(s.evidence_type, '')
                    || '; confidence=' || COALESCE(s.confidence_level, '')
                    || CASE WHEN s.notes IS NOT NULL THEN '; notes=' || s.notes ELSE '' END
                    AS description,
                'Compiled forcing event record; UBY annotation added by uby-time.' AS attribution
            FROM {alias}.{table} AS s
            WHERE NOT EXISTS (
                SELECT 1
                FROM main.uby_events AS u
                WHERE u.source_dataset = s.source_compilation
                  AND u.source_record_id = s.source_record_id
                  AND u.event_name = s.event_name
            )
            """,
            label,
        )
        return label, source_count, inserted
    finally:
        detach_database(cursor, alias)


def merge_mass_extinction_lag_tables(cursor: sqlite3.Cursor) -> list[tuple[str, int, int]]:
    """合并 mass-extinction lag 数据库中的事件表，避免合并派生 pair 表。"""
    source_db = PROCESSED_DIR / "uby_mass_extinction_lag.sqlite"
    alias = "src_mass_extinction"
    tables = ["extinction_events", "forcing_events"]
    results: list[tuple[str, int, int]] = []

    print("\n3. 合并 Mass Extinction Lag 数据集...")
    if not attach_database(cursor, source_db, alias):
        return [(f"Mass Extinction Lag {table}", 0, 0) for table in tables]

    try:
        columns = ", ".join(UBY_EVENT_COLUMNS)
        for table in tables:
            label = f"Mass Extinction Lag {table}"
            if not table_exists(cursor, table, alias):
                print(f"  跳过: 源表不存在: {table}")
                results.append((label, 0, 0))
                continue

            source_count = get_count(cursor, table, alias)
            inserted = insert_select(
                cursor,
                f"""
                SELECT {columns}
                FROM {alias}.{table} AS s
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM main.uby_events AS u
                    WHERE u.source_dataset = s.source_dataset
                      AND u.source_record_id = s.source_record_id
                      AND u.event_name = s.event_name
                )
                """,
                label,
            )
            results.append((label, source_count, inserted))
        return results
    finally:
        detach_database(cursor, alias)


def write_reports(
    initial_count: int,
    final_count: int,
    merge_results: Iterable[tuple[str, int, int]],
) -> None:
    results = list(merge_results)
    source_records_seen = sum(source_count for _, source_count, _ in results)
    inserted_records = sum(inserted for _, _, inserted in results)

    report = {
        "merge_timestamp": datetime.now().isoformat(),
        "unified_database": str(UNIFIED_DB),
        "initial_count": initial_count,
        "final_count": final_count,
        "new_records_added": final_count - initial_count,
        "inserted_records_reported_by_steps": inserted_records,
        "source_records_seen": source_records_seen,
        "merged_datasets": [
            {
                "dataset": label,
                "source_records": source_count,
                "inserted_records": inserted,
                "skipped_as_duplicates": source_count - inserted,
            }
            for label, source_count, inserted in results
        ],
        "deduplication_key": ["source_dataset", "source_record_id", "event_name"],
    }

    json_path = PROCESSED_DIR / "dataset_merge_report.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    md_path = PROCESSED_DIR / "dataset_integration_report.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# UBY数据集合并报告\n\n")
        f.write("## 概述\n\n")
        f.write("新的数据集已按统一 `uby_events` 模式合并到 UBY 统一时间线数据库中。\n\n")
        f.write("## 合并统计\n\n")
        f.write(f"- **合并时间**: {report['merge_timestamp']}\n")
        f.write(f"- **统一数据库**: `{UNIFIED_DB}`\n")
        f.write(f"- **合并前记录数**: {initial_count:,}\n")
        f.write(f"- **合并后记录数**: {final_count:,}\n")
        f.write(f"- **本次新增记录数**: {final_count - initial_count:,}\n")
        f.write(f"- **源记录总数**: {source_records_seen:,}\n")
        f.write(f"- **去重键**: `source_dataset + source_record_id + event_name`\n\n")
        f.write("## 数据集明细\n\n")
        f.write("| 数据集 | 源记录数 | 新增记录数 | 已存在/跳过 |\n")
        f.write("|---|---:|---:|---:|\n")
        for label, source_count, inserted in results:
            f.write(
                f"| {label} | {source_count:,} | {inserted:,} | {source_count - inserted:,} |\n"
            )
        f.write("\n## 符合性说明\n\n")
        f.write("- 保留原始时间字段与数据来源字段。\n")
        f.write("- 将异构源表统一映射到 `uby_events` 的事件、时间、UBY标记、精度、溯源字段。\n")
        f.write("- 合并过程具备幂等性，重复运行不会按同一去重键重复插入记录。\n")
        f.write("- 合并后执行 `REINDEX` 以刷新现有查询索引。\n")

    print(f"\n合并报告已保存到: {json_path}")
    print(f"集成报告已更新到: {md_path}")


def merge_datasets_to_unified() -> None:
    """将新数据集合并到 UBY 统一数据库中。"""

    if not UNIFIED_DB.exists():
        raise FileNotFoundError(f"统一数据库不存在: {UNIFIED_DB}")

    conn_unified = sqlite3.connect(UNIFIED_DB)
    cursor = conn_unified.cursor()

    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA foreign_keys=OFF")

        if not table_exists(cursor, "uby_events"):
            raise RuntimeError("统一数据库中不存在 uby_events 表")

        print(f"开始合并新数据集到统一数据库: {UNIFIED_DB}")

        cursor.execute("SELECT COUNT(*) FROM uby_events")
        initial_count = int(cursor.fetchone()[0])
        print(f"合并前统一数据库记录数: {initial_count:,}")

        merge_results: list[tuple[str, int, int]] = []
        merge_results.append(merge_pbdb_collections(cursor))
        merge_results.append(merge_uby_forcing_events(cursor))
        merge_results.extend(merge_mass_extinction_lag_tables(cursor))

        conn_unified.commit()

        cursor.execute("SELECT COUNT(*) FROM uby_events")
        final_count = int(cursor.fetchone()[0])

        print("\n更新数据库索引...")
        cursor.execute("REINDEX")
        conn_unified.commit()

        print("\n=== 数据集合并完成 ===")
        print(f"合并前记录数: {initial_count:,}")
        print(f"合并后记录数: {final_count:,}")
        print(f"新增记录数: {final_count - initial_count:,}")

        print("\n合并的数据集:")
        for label, source_count, inserted in merge_results:
            print(
                f"  - {label}: 源记录 {source_count:,}，新增 {inserted:,}，"
                f"跳过 {source_count - inserted:,}"
            )

        write_reports(initial_count, final_count, merge_results)

    except Exception:
        conn_unified.rollback()
        raise
    finally:
        conn_unified.close()


if __name__ == "__main__":
    merge_datasets_to_unified()
