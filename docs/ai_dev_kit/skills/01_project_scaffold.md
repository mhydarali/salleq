# Goal

Create the Databricks-native project scaffold for `salleq_symptom_routing_agent`.

# Files To Create Or Modify

- `AGENTS.md`
- `README.md`
- `requirements.txt`
- `databricks.yml`
- package directories under `src/`
- notebooks under `notebooks/`
- tests under `tests/`

# Acceptance Criteria

- The project follows the required directory structure.
- `AGENTS.md` exists and defines strict safety and JSON-contract rules.
- `README.md` explains purpose, deployment, testing, and frontend integration.
- `databricks.yml` is valid bundle-style configuration.
- Source directories are importable.

# Validation Steps

1. Confirm the directory tree exists.
2. Run `python -m py_compile` on the Python modules.
3. Verify the workspace upload path is documented in `README.md`.
