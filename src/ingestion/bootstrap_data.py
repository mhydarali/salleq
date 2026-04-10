from __future__ import annotations

from typing import Any

from src.ingestion.facility_master_ingest import FacilityMasterRecord, load_facility_master
from src.ingestion.qc_er_scraper import build_bronze_rows, build_gold_rows, build_silver_rows, fetch_quebec_er_records
from src.matching.facility_matcher import MasterFacility, match_live_facility
from src.utils.config import settings
from src.utils.text import now_utc_iso


def build_master_candidates(master_records: list[FacilityMasterRecord]) -> list[MasterFacility]:
    return [
        MasterFacility(
            facility_id_normalized=record.facility_id_normalized,
            facility_name=record.facility_name,
            full_address=record.full_address,
            city=record.city,
        )
        for record in master_records
    ]


def build_match_rows(candidates: list[MasterFacility], live_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    match_rows: list[dict[str, Any]] = []
    for row in live_rows:
        result = match_live_facility(row["facility_name_raw"], row["address_raw"], candidates)
        match_rows.append(
            {
                "facility_name_raw": row["facility_name_raw"],
                "address_raw": row["address_raw"],
                "matched_facility_id": result.matched_facility_id,
                "matched_facility_name": result.matched_facility_name,
                "match_confidence": result.match_confidence,
                "match_method": result.match_method,
                "manually_validated": False,
                "matched_at": row["scraped_at"],
            }
        )
    return match_rows


def apply_manual_overrides(
    match_rows: list[dict[str, Any]],
    override_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    override_map = {
        (str(row.get("facility_name_raw", "")), str(row.get("address_raw", ""))): row for row in override_rows
    }
    updated_rows: list[dict[str, Any]] = []
    for row in match_rows:
        override = override_map.get((str(row["facility_name_raw"]), str(row["address_raw"])))
        if override:
            updated_rows.append(
                {
                    **row,
                    "matched_facility_id": override.get("matched_facility_id"),
                    "matched_facility_name": override.get("matched_facility_name"),
                    "match_confidence": 1.0,
                    "match_method": "manual_override",
                    "manually_validated": True,
                }
            )
        else:
            updated_rows.append(row)
    return updated_rows


def bootstrap_payload() -> dict[str, Any]:
    scraped_at = now_utc_iso()
    facility_master = load_facility_master(settings.facility_master_source_url)
    live_records = fetch_quebec_er_records(settings.qc_source_url, scraped_at)
    live_rows = build_gold_rows(live_records)
    match_rows = build_match_rows(build_master_candidates(facility_master), live_rows)
    return {
        "scraped_at": scraped_at,
        "facility_master": [record.__dict__ for record in facility_master],
        "bronze_rows": build_bronze_rows(live_records),
        "silver_rows": build_silver_rows(live_records),
        "live_rows": live_rows,
        "match_rows": match_rows,
    }
