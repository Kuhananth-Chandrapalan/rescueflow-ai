# Strictly free-tier deployment

- **Dashboard:** Streamlit Community Cloud free public app; connect GitHub and choose `app.py`, using Python 3.12. Community deployments have resource and availability constraints.
- **ML:** Scikit-learn local RandomForest. No LLM API key is required to *run the dashboard*.
- **Weather:** Optional Open-Meteo API for non-commercial projects, no API key, CC BY 4.0 attribution required. It is disabled by default.
- **CI:** Standard GitHub-hosted Actions runners in public repositories are free under GitHub's terms and fair usage. Avoid private-repo paid minutes, large artifacts or paid infrastructure.
- **Daily AI edits:** Gemini API free-tier only. Use a Google AI Studio free-tier key and **do not enable paid billing**. Per-account/model free limits can change; a failure should stop creation of the PR, never upgrade automatically.
- **GitHub token:** Built-in `GITHUB_TOKEN`, scoped to one repository, creates PRs. No broad PAT or cross-repository token is necessary for daily features in this project.
- **Repo creation:** Run `gh repo create` locally after authenticating in your own GitHub CLI. An Actions token scoped to an existing repository cannot create new account-wide repositories. Automatic cross-repo creation requires a separate, more powerful credential; avoid it until the project catalog and permissions are audited.
- **Data privacy:** Free Gemini requests may be used to improve the provider's products. Use only public, non-sensitive source snippets and synthetic example data.
