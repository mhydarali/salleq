from src.matching.facility_matcher import MasterFacility, match_live_facility


def test_match_live_facility_prefers_same_name_and_address():
    result = match_live_facility(
        "Centre hospitalier de l'Université de Montréal",
        "1000 rue Saint-Denis, Montréal, H2X 0A9",
        [
            MasterFacility("chum", "Centre hospitalier de l'Université de Montréal", "1000 rue Saint-Denis, Montréal, H2X 0A9", "Montréal"),
            MasterFacility("stmary", "Centre hospitalier de St.Mary", "3830 avenue Lacombe, Montréal, H3T 1M5", "Montréal"),
        ],
    )
    assert result.matched_facility_id == "chum"
    assert result.match_confidence > 0.9
