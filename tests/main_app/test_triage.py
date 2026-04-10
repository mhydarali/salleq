from src.agents.triage_rules import assess_symptoms


def test_assess_symptoms_flags_emergency_stop():
    result = assess_symptoms("Chest pain with shortness of breath and severe sweating", "adult")
    assert result.emergency_stop is True
    assert result.provisional_ctas_level <= 2


def test_assess_symptoms_allows_queue_for_low_acuity():
    result = assess_symptoms("Mild ankle sprain after walking, minor swelling for 4 hours", "adult")
    assert result.provisional_ctas_level >= 4
