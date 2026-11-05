# 30-day reviewed AI engineering roadmap

The full task queue is `tasks/backlog.json`. One meaningful task is proposed per scheduled run. A second run does not create another PR while an `automation/*` PR remains open. The approved queue finishes after 30 tasks; it does not invent filler commits.

## Stage A — Model reliability (days 1–4)
Prediction intervals, stockout scoring, true multi-horizon backtesting, controlled calendar/promotion effects.

## Stage B — Operations and supply constraints (days 5–12)
Supplier pack sizes, multi-location inventory, expiry lots, anomaly detection, lead time uncertainty, scenario comparison, reorder explanations, budget frontier.

## Stage C — Rescue allocation and climate impact (days 13–17)
Waste risk, carbon factors, recipient matching, cluster-based routing suggestions, weather data health.

## Stage D — ML observability and reporting (days 18–24)
Distribution drift, explainability, report export, quality dashboard, feedback, baselines, turnover.

## Stage E — Responsible release hardening (days 25–30)
Fairness diagnostics, stress tests, interval calibration, input onboarding, performance, deployment gates.

## Second planned large project

**MatchWise AI — explainable supply/demand recommendation dashboard.** A local-content or nonprofit resource-matching recommendation engine, with cold-start baseline, offline ranking metrics, transparent preference controls, diversity/coverage reporting, and protected-feature exclusion. Separate repository and validated input data required before activation. Do not manufacture real-user click data.

## Third planned large project

**EnergyPilot AI — energy-use forecasting and anomaly diagnostics.** A time-series dashboard for facility consumption, weather and tariff scenarios, peak warnings and explainable actions. Real smart meter or open licensed datasets required for claims about operational savings.

Deploy each independent project as a public portfolio repo, but keep one daily agent enabled at a time if your Gemini free-tier quota is limited. Future multi-repository orchestration should explicitly rotate projects and gate new repository creation rather than giving the model unrestricted account-level rights.
