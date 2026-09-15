# Jair Ribeiro — Career Story

A Streamlit personal site built as a human career story rather than a CV.

## Site structure

- About
- Expertise
- Career
- Blog
- Get in contact

## Runtime

- Python 3.12
- Streamlit 1.53.0
- Entrypoint: `app.py`
- No application secrets required
- No external Linux packages required

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## GitHub development environment

The repository includes a Codespaces configuration under `.devcontainer/`. Every push or pull request to `main` runs `.github/workflows/streamlit-ci.yml`, which installs dependencies, compiles the application, validates the embedded site bundle, starts Streamlit, and checks its health endpoint.

## Publish with Streamlit Community Cloud

Deploy with:

- Repository: `AIribeiro/careersite`
- Branch: `main`
- Main file: `app.py`
- Python: `3.12`

The visual site source and optimized photography are packed into text-safe payload chunks under `payload_parts/`, so deployment has no external asset dependency.
