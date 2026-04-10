from __future__ import annotations

import unittest

from src.symptom_routing.assistant.tools import build_routing_decision, validate_output_shape


class AgentContractTests(unittest.TestCase):
    def test_output_shape_is_valid_for_english_input(self) -> None:
        result = build_routing_decision(
            "Twisted ankle with swelling after a fall",
            patient_age_group="adult",
            explicit_duration_hours=4,
        )
        validate_output_shape(result)
        self.assertEqual(result["language"], "en")

    def test_output_shape_is_valid_for_french_input(self) -> None:
        result = build_routing_decision(
            "Mal de gorge et fievre depuis un jour",
            patient_age_group="child",
            explicit_duration_hours=24,
        )
        validate_output_shape(result)
        self.assertEqual(result["language"], "fr")


if __name__ == "__main__":
    unittest.main()
