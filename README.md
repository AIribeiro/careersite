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
- No application secrets are required
- No external Linux packages are required

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

## GitHub development environment

The repository includes a `.devcontainer/devcontainer.json` configuration. In GitHub, choose **Code → Codespaces → Create codespace on main**. The environment installs the Python dependencies automatically and exposes Streamlit on port 8501.

Every push or pull request to `main` runs `.github/workflows/streamlit-ci.yml`. The workflow installs the pinned dependencies, compiles the application, validates the embedded site bundle, starts Streamlit, and checks its health endpoint.

## Publish with Streamlit Community Cloud

This repository is the deployment source. In Streamlit Community Cloud create an app with:

- Repository: `AIribeiro/careersite`
- Branch: `main`
- Main file path: `app.py`
- Python: `3.12`

No secrets need to be entered. Once deployed, Streamlit Community Cloud watches the GitHub repository and redeploys after commits to the configured branch.

## Repository layout

```text
.
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       └── streamlit-ci.yml
├── .streamlit/
│   └── config.toml
├── payload_parts/
│   └── part_*.b64
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

The visual site source and optimized image assets are packed into text-safe payload chunks under `payload_parts/`. `app.py` reconstructs the bundle in memory at runtime, preserving the site design and photography without external asset hosting.
