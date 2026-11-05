# Windows / VS Code setup walkthrough

1. Download and extract `rescueflow_ai.zip` to Downloads. In VS Code, open the **inner `rescueflow_ai` folder** (the folder containing `app.py`, `bootstrap_github.ps1` and `requirements.txt`).
2. Open Terminal → New Terminal (PowerShell).
3. Run `python -m venv .venv`. Run `.\.venv\Scripts\Activate.ps1`. If Windows blocks script activation, use `.\.venv\Scripts\python.exe` explicitly instead; avoid changing system-wide execution policies.
4. Run `python -m pip install -r requirements.txt pytest` and `python -m pytest -q`. You should see 16 passing tests for this release.
5. Run `streamlit run app.py`. Your browser shows the dashboard, usually at `http://localhost:8501`.
6. Install GitHub CLI once if necessary with `winget install --id GitHub.cli`. In a **new terminal**, run `gh auth login` and `gh auth status`. Confirm your GitHub login is `Kuhananth-Chandrapalan`, not a previous account.
7. Run `.\bootstrap_github.ps1`. This creates and pushes the public repository `Kuhananth-Chandrapalan/rescueflow-ai`, as long as it does not already exist. If the repository already exists, stop and inspect before pushing.
8. Add the Gemini **free-tier** API key as the `GEMINI_API_KEY` Actions secret to the new repository. Do not enable paid billing, and do not share the key in chat or source control.
9. In repository Settings → Actions → General, permit Actions to create pull requests. Then select Actions → Daily AI Engineering Auto-Merge → Run workflow, branch `main`.
10. Review its PR and merge only if the changes and tests are credible. The scheduler will run at 8:17 AM Sri Lanka time, unless an automated PR is still awaiting review.

The app itself does not need the Gemini key. Gemini is used only to *write new code* during the daily workflow.
