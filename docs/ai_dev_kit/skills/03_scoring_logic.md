# Goal

Implement deterministic routing logic for emergency detection, provisional CTAS assignment, and risk scoring.

# Files To Create Or Modify

- `src/scoring/emergency_logic.py`
- `src/scoring/ctas_logic.py`
- `src/scoring/risk_score.py`
- `src/utils/parsing.py`

# Acceptance Criteria

- Emergency red flags trigger hard stops.
- CTAS logic is conservative and prefers higher acuity when uncertain.
- Risk scoring uses the specified weighted formula.
- Queue eligibility follows the routing policy.

# Validation Steps

1. Run unit tests for emergency and CTAS cases.
2. Verify CTAS 1 and 2 never allow queue eligibility.
3. Verify CTAS 4 and 5 can become queue eligible when risk is low.
