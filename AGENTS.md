# RescueFlow AI — Developer and AI agent guardrails

RescueFlow solves a concrete problem: reduce food shortages and waste by combining demand forecasting, budget-aware replenishment and transparent donation screening.

## Integrity and safety rules

- Never claim synthetic demand/inventory/emissions to be real operational data.
- Forecasts are fallible. Review recommendations with human operators; no autonomous food distribution or procurement actions.
- Do not fake improvements, benchmarks, citations or datasets.
- Add user-visible functionality to existing application entrypoints, not disconnected demo files.
- Use standard library and dependencies already declared in requirements.txt; automated agent cannot edit dependencies.
- Agent may edit only `app.py`, `src/**/*.py`, `tests/**/*.py`, and `docs/**/*.md`.
- Agent cannot alter GitHub Actions, Git metadata, credentials, automation, tasks, requirements or configuration.
- For each task add meaningful tests, error handling, documentation and evidence of behavior.
- Do not connect to paid APIs or services. Open-Meteo is permitted only for non-commercial use with attribution.
- Avoid privacy-sensitive real data, credentials, precise personal locations and unsafe food safety conclusions.
- This demo project may automatically merge AI-generated changes only after the trusted validation jobs pass; do not treat green tests as a safety certification. Do not automate real procurement, donations or food-safety decisions.
