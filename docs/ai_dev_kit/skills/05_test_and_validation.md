# Goal

Create notebooks and tests that verify the routing engine is safe, deterministic, and frontend-ready.

# Files To Create Or Modify

- `notebooks/setup.py`
- `notebooks/test_agent.py`
- `notebooks/validate_risk_logic.py`
- `notebooks/demo_examples.py`
- `tests/test_emergency_logic.py`
- `tests/test_risk_score.py`
- `tests/test_agent_contract.py`

# Acceptance Criteria

- Emergency-stop rules are covered by tests.
- English and French examples are covered.
- JSON output contract is validated.
- Notebooks demonstrate setup, validation, and frontend handoff.

# Validation Steps

1. Run `python -m unittest discover -s tests`.
2. Run the Databricks notebooks in order.
3. Verify the simulated-case table contains all risk bands and CTAS levels.
