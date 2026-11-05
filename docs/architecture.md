# Architecture and honest evaluation

## Domain problem

Small food retailers face a coupled problem: uncertain demand causes both stockouts and spoilage. Procurement competes for a fixed budget, while surplus can only be rescued if food is safe and there is genuine recipient capacity.

## Modules

- `src/rescueflow/demo.py` — deterministic, explicitly synthetic store, inventory and daily demand data.
- `src/rescueflow/forecast.py` — calendar + weather + lag supervised random forest; chronological rolling 1-step evaluation; iterative 7-14-day future inference.
- `src/rescueflow/decisions.py` — auditable approximate purchasing under a hard cost cap and shelf-life proxy; donation screening.
- `src/rescueflow/validation.py` — strict schemas and time continuity checks.
- `src/rescueflow/weather.py` — optional free non-commercial Open-Meteo forecast without key, with attribution.
- `app.py` — dashboard for operators, analysts and portfolio reviewers.
- `automation/` — curated daily development agent and GitHub PR pipeline. No model writes to git itself.

## Data and evaluation

The included demo does *not* establish actual model quality on production distribution. Its demand is generated with controlled calendar/weather patterns and noise. Only a chronology-based 28-day holdout is used. Features for each holdout day use prior actual observed demand, making this a **rolling one-day-ahead** test; this is not a direct long-range test. Real deployment demands horizon-specific walk-forward evaluation, measured costs, calibration and actual business data.

## Optimization limitations

Replenishment is a **greedy budgeted priority heuristic**, not a globally optimal mixed-integer solution. Donation candidates are estimates only, not operational instructions. Real decisions require expiry lots, cold-chain compliance, local food regulations, supplier MOQs, vehicle routes and recipient constraints.

## Safety and execution isolation

Model code generation is restricted to source, tests and documentation. Generated tests run in the **develop job with read-only GitHub permissions**. The publisher job has a write token but **never executes the generated Python code**. Its only code execution is trusted `automation/guard_changes.py` and `automation/mark_complete.py` already on `main`. The PR is review-only and waits for a human merge. This is a prototype security boundary, not a substitute for full sandbox isolation and code review.
