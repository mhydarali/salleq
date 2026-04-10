from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Iterable

import httpx
from bs4 import BeautifulSoup

from src.utils.text import make_id, normalize_text, parse_duration_to_minutes, parse_metric_int, parse_metric_pct


@dataclass
class QuebecERRecord:
    scrape_id: str
    facility_name_raw: str
    address_raw: str
    region: str
    wait_time_non_priority_minutes: int | None
    people_waiting: int | None
    total_people_er: int | None
    stretcher_occupancy_pct: float | None
    avg_wait_room_minutes_prev_day: int | None
    avg_stretcher_wait_minutes_prev_day: int | None
    raw_html_fragment: str
    source_url: str
    scraped_at: str


def _extract_metric_map(block: BeautifulSoup) -> dict[str, str]:
    metrics: dict[str, str] = {}
    for item in block.select("li.hopital-item"):
        text = " ".join(item.stripped_strings)
        if ":" not in text:
            continue
        label, value = text.split(":", 1)
        metrics[normalize_text(label)] = value.strip()
    return metrics


def _extract_page_urls(soup: BeautifulSoup, base_url: str) -> list[str]:
    page_urls = {base_url}
    for anchor in soup.select("a[data-page]"):
        href = anchor.get("href")
        if not href:
            continue
        if href.startswith("http"):
            page_urls.add(href)
        else:
            page_urls.add(f"https://www.quebec.ca{href}")
    return sorted(page_urls)


def parse_er_page(html: str, source_url: str, scraped_at: str) -> list[QuebecERRecord]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[QuebecERRecord] = []
    for element in soup.select("div.hospital_element"):
        title = element.select_one("li.title .font-weight-bold")
        address = element.select_one("div.adresse")
        if not title or not address:
            continue
        address_lines = list(address.stripped_strings)
        address_raw = address_lines[0] if address_lines else ""
        region = address_lines[1] if len(address_lines) > 1 else ""
        metrics = _extract_metric_map(element)
        records.append(
            QuebecERRecord(
                scrape_id=make_id("scrape"),
                facility_name_raw=title.get_text(strip=True),
                address_raw=address_raw,
                region=region,
                wait_time_non_priority_minutes=parse_duration_to_minutes(
                    metrics.get(normalize_text("Estimated waiting time for non-priority cases to see a doctor"))
                ),
                people_waiting=parse_metric_int(
                    metrics.get(normalize_text("Number of people waiting to see a doctor in the emergency room"))
                ),
                total_people_er=parse_metric_int(
                    metrics.get(normalize_text("Total number of people in the emergency room"))
                ),
                stretcher_occupancy_pct=parse_metric_pct(
                    metrics.get(normalize_text("Occupancy rate of stretchers"))
                ),
                avg_wait_room_minutes_prev_day=parse_duration_to_minutes(
                    metrics.get(normalize_text("Average time in the waiting room (from the previous day)"))
                ),
                avg_stretcher_wait_minutes_prev_day=parse_duration_to_minutes(
                    metrics.get(normalize_text("Average waiting time on a stretcher (from the previous day)"))
                ),
                raw_html_fragment=str(element),
                source_url=source_url,
                scraped_at=scraped_at,
            )
        )
    return records


def fetch_quebec_er_records(source_url: str, scraped_at: str, timeout: float = 30.0) -> list[dict[str, object]]:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        first_page = client.get(source_url)
        first_page.raise_for_status()
        soup = BeautifulSoup(first_page.text, "html.parser")
        page_urls = _extract_page_urls(soup, source_url)
        seen: set[tuple[str, str]] = set()
        parsed: list[dict[str, object]] = []
        for page_url in page_urls:
            response = client.get(page_url)
            response.raise_for_status()
            for record in parse_er_page(response.text, page_url, scraped_at):
                key = (record.facility_name_raw, record.address_raw)
                if key in seen:
                    continue
                seen.add(key)
                parsed.append(asdict(record))
        return parsed


def build_gold_rows(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "scrape_id": record["scrape_id"],
            "facility_name_raw": record["facility_name_raw"],
            "address_raw": record["address_raw"],
            "region": record["region"],
            "wait_time_non_priority_minutes": record["wait_time_non_priority_minutes"],
            "people_waiting": record["people_waiting"],
            "total_people_er": record["total_people_er"],
            "stretcher_occupancy_pct": record["stretcher_occupancy_pct"],
            "avg_wait_room_minutes_prev_day": record["avg_wait_room_minutes_prev_day"],
            "avg_stretcher_wait_minutes_prev_day": record["avg_stretcher_wait_minutes_prev_day"],
            "source_url": record["source_url"],
            "scraped_at": record["scraped_at"],
        }
        for record in records
    ]


def build_silver_rows(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    silver_rows: list[dict[str, object]] = []
    for row in build_gold_rows(records):
        silver_rows.append(
            {
                **row,
                "normalized_facility_name": normalize_text(str(row["facility_name_raw"])),
                "normalized_address": normalize_text(str(row["address_raw"])),
            }
        )
    return silver_rows


def build_bronze_rows(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    bronze_rows: list[dict[str, object]] = []
    for record in records:
        bronze_rows.append(
            {
                "scrape_id": record["scrape_id"],
                "source_url": record["source_url"],
                "raw_html_fragment": record.get("raw_html_fragment", ""),
                "facility_name_raw": record["facility_name_raw"],
                "address_raw": record["address_raw"],
                "region_raw": record["region"],
                "metric_payload": json.dumps(
                    {
                        "wait_time_non_priority_minutes": record["wait_time_non_priority_minutes"],
                        "people_waiting": record["people_waiting"],
                        "total_people_er": record["total_people_er"],
                        "stretcher_occupancy_pct": record["stretcher_occupancy_pct"],
                        "avg_wait_room_minutes_prev_day": record["avg_wait_room_minutes_prev_day"],
                        "avg_stretcher_wait_minutes_prev_day": record["avg_stretcher_wait_minutes_prev_day"],
                    },
                    ensure_ascii=True,
                ),
                "scraped_at": record["scraped_at"],
            }
        )
    return bronze_rows


def records_to_rows(records: Iterable[dict[str, object]]) -> list[tuple[object, ...]]:
    return [
        (
            record["scrape_id"],
            record["facility_name_raw"],
            record["address_raw"],
            record["region"],
            record["wait_time_non_priority_minutes"],
            record["people_waiting"],
            record["total_people_er"],
            record["stretcher_occupancy_pct"],
            record["avg_wait_room_minutes_prev_day"],
            record["avg_stretcher_wait_minutes_prev_day"],
            record["source_url"],
            record["scraped_at"],
        )
        for record in records
    ]
