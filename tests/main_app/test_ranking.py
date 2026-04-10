from src.ranking.facility_ranker import FacilityCandidate, rank_facilities


def test_rank_facilities_penalizes_ambulatory_for_higher_acuity():
    ranked = rank_facilities(
        [
            FacilityCandidate("hospital", "Hospital", "hospital", "Montreal", 45.5, -73.5, 120, 15, 95, 40, 8),
            FacilityCandidate("ambulatory", "Clinic", "ambulatory", "Montreal", 45.52, -73.52, 25, 2, 5, 4, 1),
        ],
        provisional_ctas_level=3,
        user_latitude=45.51,
        user_longitude=-73.51,
    )
    assert ranked[0].facility_id_normalized == "hospital"
