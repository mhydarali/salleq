# Goal

Wrap the deterministic routing engine in a Mosaic AI `ResponsesAgent` with strict JSON output.

# Files To Create Or Modify

- `src/assistant/system_prompt.txt`
- `src/assistant/output_schema.json`
- `src/assistant/tools.py`
- `src/assistant/agent.py`

# Acceptance Criteria

- The system prompt forbids diagnosis, treatment advice, and non-JSON output.
- The output schema matches the required frontend contract exactly.
- The tool layer assembles a complete routing decision deterministically.
- The agent returns JSON-only output items.

# Validation Steps

1. Run sample English and French requests.
2. Validate the returned payload against the JSON contract.
3. Confirm emergency examples return `emergency_stop = true`.
