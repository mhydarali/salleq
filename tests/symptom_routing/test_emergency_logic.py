from __future__ import annotations

import unittest

from src.symptom_routing.assistant.tools import build_routing_decision


class EmergencyLogicTests(unittest.TestCase):
    def test_emergency_cases_stop_the_flow(self) -> None:
        result = build_routing_decision(
            "Chest pain and severe difficulty breathing for one hour",
            patient_age_group="adult",
            explicit_duration_hours=1,
        )
        self.assertTrue(result["emergency_stop"])
        self.assertFalse(result["queue_eligible"])
        self.assertEqual(result["recommended_facility_type"], "hospital")
        self.assertEqual(result["recommended_urgency_band"], "emergency")
        self.assertEqual(result["risk_score"], 100)

    def test_infant_fever_is_high_risk(self) -> None:
        result = build_routing_decision(
            "Infant fever with poor feeding for 6 hours",
            patient_age_group="infant",
            explicit_duration_hours=6,
        )
        self.assertTrue(result["emergency_stop"])
        self.assertIn("high-risk infant symptoms", result["emergency_flags"])

    def test_loss_of_consciousness_routes_to_ctas_one(self) -> None:
        result = build_routing_decision(
            "Loss of consciousness with blue lips",
            patient_age_group="adult",
            explicit_duration_hours=1,
        )
        self.assertEqual(result["provisional_ctas_level"], 1)
        self.assertTrue(result["emergency_stop"])
        self.assertFalse(result["queue_eligible"])


if __name__ == "__main__":
    unittest.main()
