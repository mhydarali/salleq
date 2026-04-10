from __future__ import annotations

import unittest

from src.symptom_routing.assistant.tools import build_routing_decision


class RiskScoreTests(unittest.TestCase):
    def test_ctas_one_and_two_never_queue(self) -> None:
        chest_pain = build_routing_decision(
            "Chest pain and pressure for two hours",
            patient_age_group="older_adult",
            explicit_duration_hours=2,
        )
        self.assertIn(chest_pain["provisional_ctas_level"], {1, 2})
        self.assertFalse(chest_pain["queue_eligible"])

    def test_ctas_three_routes_to_hospital_only(self) -> None:
        urgent_case = build_routing_decision(
            "Severe abdominal pain getting worse since yesterday",
            patient_age_group="adult",
            explicit_duration_hours=28,
        )
        self.assertEqual(urgent_case["provisional_ctas_level"], 3)
        self.assertFalse(urgent_case["queue_eligible"])
        self.assertEqual(urgent_case["recommended_facility_type"], "hospital")

    def test_ctas_four_or_five_can_be_queue_eligible(self) -> None:
        low_case = build_routing_decision(
            "Minor cut on hand with light bleeding, stable for 2 hours",
            patient_age_group="adult",
            explicit_duration_hours=2,
        )
        self.assertIn(low_case["provisional_ctas_level"], {4, 5})
        self.assertTrue(low_case["queue_eligible"])
        self.assertIn(low_case["recommended_facility_type"], {"hospital", "ambulatory"})


if __name__ == "__main__":
    unittest.main()
