from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.utils.text import haversine_km


@dataclass
class FacilityCandidate:
    facility_id_normalized: str
    facility_name: str
    odhf_facility_type: str | None
    city: str | None
    latitude: float | None
    longitude: float | None
    wait_time_non_priority_minutes: int | None
    people_waiting: int | None
    stretcher_occupancy_pct: float | None
    total_people_er: int | None
    virtual_queue_depth: int | None


@dataclass
class RankedFacility:
    facility_id_normalized: str
    facility_name: str
    city: str | None
    distance_km: float | None
    score: float
    fit_penalty: float
    facility_type: str | None


def _normalize(value: float | int | None, values: list[float]) -> float:
    if value is None or not values:
        return 1.0
    min_value = min(values)
    max_value = max(values)
    if max_value == min_value:
        return 0.0
    return (float(value) - min_value) / (max_value - min_value)


def _fit_penalty(ctas_level: int, facility_type: str | None) -> float:
    normalized_type = (facility_type or "").lower()
    is_ambulatory = "ambul" in normalized_type or "clinic" in normalized_type
    if ctas_level <= 2 and is_ambulatory:
        return 1.0
    if ctas_level == 3 and is_ambulatory:
        return 0.75
    if ctas_level in (4, 5) and not is_ambulatory:
        return 0.15
    return 0.0


def rank_facilities(
    candidates: Iterable[FacilityCandidate],
    provisional_ctas_level: int,
    user_latitude: float | None,
    user_longitude: float | None,
) -> list[RankedFacility]:
    candidate_list = list(candidates)
    wait_values = [float(c.wait_time_non_priority_minutes or 0) for c in candidate_list]
    distance_values = [
        float(haversine_km(user_latitude, user_longitude, c.latitude, c.longitude) or 0.0)
        for c in candidate_list
    ]
    occupancy_values = [float(c.stretcher_occupancy_pct or 0.0) for c in candidate_list]
    waiting_values = [float(c.people_waiting or 0) for c in candidate_list]
    queue_values = [float(c.virtual_queue_depth or 0) for c in candidate_list]

    ranked: list[RankedFacility] = []
    for candidate, distance in zip(candidate_list, distance_values):
        penalty = _fit_penalty(provisional_ctas_level, candidate.odhf_facility_type)
        score = (
            0.30 * _normalize(candidate.wait_time_non_priority_minutes, wait_values)
            + 0.25 * _normalize(distance, distance_values)
            + 0.20 * _normalize(candidate.stretcher_occupancy_pct, occupancy_values)
            + 0.10 * _normalize(candidate.people_waiting, waiting_values)
            + 0.10 * _normalize(candidate.virtual_queue_depth, queue_values)
            + 0.05 * penalty
        )
        ranked.append(
            RankedFacility(
                facility_id_normalized=candidate.facility_id_normalized,
                facility_name=candidate.facility_name,
                city=candidate.city,
                distance_km=distance,
                score=round(score, 4),
                fit_penalty=penalty,
                facility_type=candidate.odhf_facility_type,
            )
        )

    # Acuity fit is a hard priority signal for ordering. Score breaks ties only
    # within the same fit band so lower-acuity sites do not outrank hospitals
    # for urgent cases purely because they are faster or closer.
    return sorted(ranked, key=lambda item: (item.fit_penalty, item.score))
