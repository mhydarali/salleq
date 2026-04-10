from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from pyspark.sql import SparkSession

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.bootstrap_data import apply_manual_overrides, bootstrap_payload, build_match_rows
from src.ingestion.qc_er_scraper import build_bronze_rows, build_gold_rows, build_silver_rows, fetch_quebec_er_records
from src.matching.facility_matcher import MasterFacility
from src.utils.config import settings
from src.utils.text import now_utc_iso


def _schema_name() -> str:
    return settings.fq_schema


def _master_candidates_from_table(spark: SparkSession) -> list[MasterFacility]:
    rows = (
        spark.table(f"{_schema_name()}.facility_master")
        .select("facility_id_normalized", "facility_name", "full_address", "city")
        .collect()
    )
    return [
        MasterFacility(
            facility_id_normalized=row["facility_id_normalized"],
            facility_name=row["facility_name"],
            full_address=row["full_address"],
            city=row["city"],
        )
        for row in rows
    ]


def _manual_override_rows(spark: SparkSession) -> list[dict[str, Any]]:
    table_name = f"{_schema_name()}.manual_facility_overrides"
    if not spark.catalog.tableExists(table_name):
        return []
    return [row.asDict(recursive=True) for row in spark.table(table_name).collect()]


def _merge_match_rows(spark: SparkSession, match_rows: list[dict[str, Any]]) -> None:
    if not match_rows:
        return
    spark.createDataFrame(match_rows).createOrReplaceTempView("salleq_match_updates")
    spark.sql(
        f"""
        MERGE INTO {_schema_name()}.qc_facility_match AS target
        USING salleq_match_updates AS source
        ON target.facility_name_raw = source.facility_name_raw
           AND target.address_raw = source.address_raw
        WHEN MATCHED THEN UPDATE SET
          target.matched_facility_id = source.matched_facility_id,
          target.matched_facility_name = source.matched_facility_name,
          target.match_confidence = source.match_confidence,
          target.match_method = source.match_method,
          target.manually_validated = source.manually_validated,
          target.matched_at = source.matched_at
        WHEN NOT MATCHED THEN INSERT (
          facility_name_raw,
          address_raw,
          matched_facility_id,
          matched_facility_name,
          match_confidence,
          match_method,
          manually_validated,
          matched_at
        ) VALUES (
          source.facility_name_raw,
          source.address_raw,
          source.matched_facility_id,
          source.matched_facility_name,
          source.match_confidence,
          source.match_method,
          source.manually_validated,
          source.matched_at
        )
        """
    )


def bootstrap_tables(spark: SparkSession) -> dict[str, Any]:
    payload = bootstrap_payload()
    if not payload["live_rows"]:
        raise RuntimeError("No Quebec ER records were parsed during bootstrap.")

    spark.createDataFrame(payload["facility_master"]).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        f"{_schema_name()}.facility_master"
    )
    spark.createDataFrame(payload["bronze_rows"]).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        f"{_schema_name()}.qc_er_live_status_bronze"
    )
    spark.createDataFrame(payload["silver_rows"]).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        f"{_schema_name()}.qc_er_live_status_silver"
    )
    spark.createDataFrame(payload["live_rows"]).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        f"{_schema_name()}.qc_er_live_status"
    )
    spark.createDataFrame(payload["match_rows"]).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        f"{_schema_name()}.qc_facility_match"
    )
    return {
        "facility_master_rows": len(payload["facility_master"]),
        "live_rows": len(payload["live_rows"]),
        "match_rows": len(payload["match_rows"]),
        "scraped_at": payload["scraped_at"],
    }


def refresh_live_status(spark: SparkSession) -> dict[str, Any]:
    live_records = fetch_quebec_er_records(settings.qc_source_url, now_utc_iso())
    if not live_records:
        raise RuntimeError("No Quebec ER records were parsed during refresh.")

    bronze_rows = build_bronze_rows(live_records)
    silver_rows = build_silver_rows(live_records)
    gold_rows = build_gold_rows(live_records)
    match_rows = build_match_rows(_master_candidates_from_table(spark), gold_rows)
    match_rows = apply_manual_overrides(match_rows, _manual_override_rows(spark))

    spark.createDataFrame(bronze_rows).write.mode("append").saveAsTable(f"{_schema_name()}.qc_er_live_status_bronze")
    spark.createDataFrame(silver_rows).write.mode("append").saveAsTable(f"{_schema_name()}.qc_er_live_status_silver")
    spark.createDataFrame(gold_rows).write.mode("append").saveAsTable(f"{_schema_name()}.qc_er_live_status")
    _merge_match_rows(spark, match_rows)

    return {
        "live_rows": len(gold_rows),
        "match_rows": len(match_rows),
        "scraped_at": gold_rows[0]["scraped_at"],
    }
