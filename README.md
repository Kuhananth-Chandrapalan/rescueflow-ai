# 🌱 RescueFlow AI — Food Waste & Inventory Decision Intelligence

[![CI](https://img.shields.io/badge/CI-GitHub_Actions-4c9e91)](https://github.com/Kuhananth-Chandrapalan/rescueflow-ai/actions)

**A real-world problem-oriented ML dashboard** that forecasts demand, recommends safe-budget replenishment, and screens potential food rescue opportunities. Built as a public, free-tier portfolio project with 30 planned daily AI engineering milestones. **No paid service is required to run the dashboard.**

> **Research/demo prototype, not a deployed food safety or procurement system.** Included sales, stocks, emissions and prices are synthetic. All recommendations require human review and real-world verification.

## Main capabilities

1. Demand forecasting: reproducible time series, 12 engineered features, random forest regression, iterative next-day inference.
2. Model evaluation: last-28-day rolling 1-step test, per-SKU MAE and 7-day rolling baseline.
3. Inventory risk: lead-time shortages, safety coverage, shelf-life cap and hard replenishment budget.
4. Food rescue screening: estimate candidate surplus and indicative kilograms and carbon factors (not verified carbon savings).
5. Scenario intelligence: shift temperature, planning days, safety buffer and budget interactively.
6. Data onboarding: validated history/inventory CSV upload and sample CSV downloads.
7. Weather optional: Open-Meteo, free for noncommercial use with attribution.
8. Automation: daily planned tasks implemented on isolated PR branches, independently tested, and automatically squash-merged after checks if GitHub rules allow.

## Quickstart — Windows PowerShell and Linux

Requires Python 3.12 recommended. Unzip the project and open the extracted folder in VS Code.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt pytest
python -m pytest -q
streamlit run app.py
```

On Linux/macOS, activate with `source .venv/bin/activate`.

Open the localhost URL shown by Streamlit (usually `http://localhost:8501`). No secret or real business dataset is required.

## Create the new GitHub repository and push safely

GitHub-connected ChatGPT can inspect the linked repository but may not create new account repositories because that permission is unavailable. This one-time command uses the GitHub CLI already authenticated **as you**, without sharing a token in chat:

```powershell
# If GitHub CLI isn't installed, first: winget install --id GitHub.cli
# gh auth login             # browser authorization once
# gh auth status            # verify account is Kuhananth-Chandrapalan
.\bootstrap_github.ps1
```

The script creates public `Kuhananth-Chandrapalan/rescueflow-ai`, commits this scaffold, and pushes `main`. It does not touch `devforge-ai` or `eTirri_POS`.

## Enable unattended daily development (free; autonomous merges)

1. Use your existing Google AI Studio Gemini API key from DevForge AI, if you still have its value, or create a new one in the same free-tier project. **No new key is required**; store the same key separately in the RescueFlow repository secret. The two repositories share the project quotas. Do not enable paid billing.
2. In the new repo set `Settings → Secrets and variables → Actions → New repository secret`, name `GEMINI_API_KEY`, and paste the existing key. GitHub does not reveal a saved secret; if you lost your copy, create a replacement key in Google AI Studio. Never paste keys in code/chat.
3. `Settings → Actions → General → Workflow permissions`: enable **Allow GitHub Actions to create and approve pull requests**. The workflow creates PRs and merges them after its test gates; it does not issue approval reviews.
4. In `Actions → Daily AI Engineering Auto-Merge`, choose `Run workflow` to test once.
5. If generation and both validation passes succeed, the publisher opens a PR and automatically squash-merges it into `main`; no manual PR step is needed unless repository rules block merging.
6. Then the next task is attempted daily at **8:17 AM Asia/Colombo**. If a previous automation PR remains open because GitHub rules prevented merging, the scheduler pauses rather than pile up changes.

**Note:** PRs created by `GITHUB_TOKEN` may create approval-required `pull_request` workflows and pushes do not automatically trigger normal workflow runs. The development job tests the generated code with a read-only GitHub token before the publisher opens the PR. The publisher runs the full test suite again before attempting the merge. Note that GitHub may place the PR-triggered CI in an approval-required state; this workflow does not rely on that PR event for its test gates.

## Architecture and quality

See `docs/architecture.md`, `docs/roadmap.md`, `docs/free-tier.md` and `AGENTS.md`. Run deterministic, offline unit tests with `python -m pytest -q`. This is an ML-powered decision-support dashboard, not a chatbot; its main forecasting is local and therefore does not use your free Gemini quota. Gemini is used **only for daily code-writing automation**.

## Roadmap to a large multi-project portfolio

RescueFlow is project 1. Future independent repositories: **MatchWise AI** (explainable recommendation engine) and **EnergyPilot AI** (facility energy forecasting). We will add them in stages, leaving the daily builder on one repository at a time when free API capacity is constrained. Automating *account-wide repository creation* would need additional GitHub permissions, so that part is intentionally separate from the safer daily PR mechanism.

## License & acknowledgements

MIT license for this starter's authored code. Weather data via [Open-Meteo](https://open-meteo.com/) CC BY 4.0 for non-commercial use.

## Unattended-merge safety boundary

This is an **opt-in zero-review CI mode**. The workflow creates an auditable pull request, then calls `gh pr merge --squash --match-head-commit` only after the read-only generator and isolated publisher both validate the patch, run unit tests, and check syntax. It does not use administrator bypass, auto-approval, or direct push to `main`. **Passing tests does not prove AI-generated code is correct or secure**; reserve this mode for non-sensitive demo code, watch workflow logs, and enable tighter GitHub protections before using real customer data. If required external checks, reviews, or repository rules block merging, the job fails and its PR remains open. GitHub Actions cannot override those controls.

Automated commits use the `github-actions[bot]` author and are not guaranteed to count as personal contributions. When the 30-item backlog is exhausted, the scheduler stops doing code changes until new, meaningful tasks are supplied. API free quotas and GitHub's scheduled-run availability can also interrupt daily output.
