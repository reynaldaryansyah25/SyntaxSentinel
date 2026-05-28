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

## Google Cloud and Gemini

The final product must use Google Cloud AI/Gemini for reasoning. This sprint includes `google-cloud-aiplatform` and leaves the agent service layer ready for a later Vertex AI/Gemini implementation. If Google Agent Development Kit is added later, it should be integrated behind the service layer rather than coupled directly to API endpoints.
