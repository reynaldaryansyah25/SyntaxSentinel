# SyntaxSentinel

Your autonomous first responder for broken CI/CD pipelines.

SyntaxSentinel is an MVP backend for the Google Cloud Rapid Agent Hackathon GitLab Track. It is designed to receive GitLab CI/CD failure events, inspect failing jobs, reason with Gemini on Google Cloud, and open a human-reviewable Merge Request with a small safe fix.

This first sprint sets up the FastAPI backend skeleton. The GitLab tool layer, Gemini reasoning module, safety checks, and self-healing loop will be implemented in later sprints.

## Current Scope

- FastAPI application factory in `app/main.py`
- Basic system endpoints:
  - `GET /`
  - `GET /health`
- Pydantic Settings configuration in `app/core/config.py`
- Logging setup in `app/core/logging.py`
- Shared-secret helper in `app/core/security.py`
- Initial package structure for models, services, utilities, and tests

## Project Structure

```txt
app/
  api/
    endpoints/
      system.py
    router.py
  core/
    config.py
    logging.py
    security.py
  models/
    agent.py
    gitlab.py
    response.py
  services/
    agent_engine.py
    gitlab_mcp_client.py
    orchestrator.py
    patcher.py
    safety.py
  utils/
    text.py
    traceback_parser.py
tests/
  test_system.py
.env.example
requirements.txt
README.md
verify_env.py
```

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Fill in the required values in `.env` as each sprint enables the related integration.

For GitLab development, set at least:

```env
GITLAB_BASE_URL=https://gitlab.com
GITLAB_PERSONAL_ACCESS_TOKEN=your_gitlab_personal_access_token
GITLAB_WEBHOOK_SECRET=your_random_webhook_secret
GITLAB_PROJECT_ID=your_gitlab_project_id
GITLAB_DEFAULT_BRANCH=main
DRY_RUN=true
```

For Google Cloud and Gemini, set:

```env
GCP_PROJECT_ID=your_gcp_project_id
GCP_LOCATION=us-central1
GEMINI_MODEL=your_vertex_ai_gemini_model
```

Do not commit `.env`. Use `.env.example` for safe documentation only.

## Verify Environment

Run the verification script after creating `.env`:

```bash
python verify_env.py
```

On Windows PowerShell, make sure the virtual environment is active first:

```powershell
.\.venv\Scripts\Activate.ps1
python verify_env.py
```

The script checks:

- required environment variables
- GitLab token validity through the GitLab `/api/v4/user` endpoint
- Vertex AI configuration initialization
- Google Application Default Credentials, when available

Secrets are never printed. The script exits with a non-zero code if required credentials or configuration are missing.

If Google Cloud billing or Application Default Credentials are not ready yet, GitLab checks can still pass while the final summary fails. Finish Google Cloud setup before live Gemini or Cloud Run usage.

## Run Locally

Start the development server:

```bash
uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`

## Run Tests

```bash
pytest
```

## Configuration

The application reads environment variables through Pydantic Settings. See `.env.example` for the supported values.

Secrets such as GitLab tokens and webhook secrets must stay in `.env` or a secret manager. Do not commit real secrets to the repository.

## Troubleshooting GitLab Token Verification

If `python verify_env.py` reports that the GitLab token is invalid:

- Confirm the token was copied completely. GitLab personal access tokens often start with `glpat-`.
- Confirm the token has the `api` scope. `read_user` is useful, but `api` is required for later repository and Merge Request actions.
- Confirm the token is not expired or revoked in GitLab user settings.
- Confirm `GITLAB_BASE_URL` is `https://gitlab.com` for GitLab.com projects.
- Confirm the project ID in `GITLAB_PROJECT_ID` belongs to a project your account can access.
- Generate a new token if the old token may have been exposed. Never paste real tokens into issues, README files, screenshots, or chat.

## Google Cloud and Gemini

The final product must use Google Cloud AI/Gemini for reasoning. This sprint includes `google-cloud-aiplatform` and leaves the agent service layer ready for a later Vertex AI/Gemini implementation. If Google Agent Development Kit is added later, it should be integrated behind the service layer rather than coupled directly to API endpoints.
