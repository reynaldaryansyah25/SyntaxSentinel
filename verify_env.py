import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

from app.core.config import get_settings


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str


def print_result(result: CheckResult) -> None:
    marker = "[OK]" if result.ok else "[FAIL]"
    print(f"{marker} {result.name}: {result.message}")


def print_warn(name: str, message: str) -> None:
    print(f"[WARN] {name}: {message}")


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def check_required_settings() -> list[CheckResult]:
    settings = get_settings()
    required = {
        "GITLAB_PERSONAL_ACCESS_TOKEN": settings.gitlab_personal_access_token,
        "GITLAB_WEBHOOK_SECRET": settings.gitlab_webhook_secret,
        "GITLAB_PROJECT_ID": settings.gitlab_project_id,
        "GCP_PROJECT_ID": settings.gcp_project_id,
        "GCP_LOCATION": settings.gcp_location,
        "GEMINI_MODEL": settings.gemini_model,
    }

    results: list[CheckResult] = []
    for name, value in required.items():
        results.append(
            CheckResult(
                name=name,
                ok=has_value(value),
                message="configured" if has_value(value) else "missing",
            )
        )
    return results


async def check_gitlab_token() -> CheckResult:
    try:
        import httpx
    except ImportError:
        return CheckResult("GitLab token", False, "httpx is not installed; run pip install -r requirements.txt")

    settings = get_settings()
    if not settings.gitlab_personal_access_token:
        return CheckResult("GitLab token", False, "missing token")

    user_url = urljoin(settings.gitlab_base_url.rstrip("/") + "/", "api/v4/user")
    headers = {"PRIVATE-TOKEN": settings.gitlab_personal_access_token}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(user_url, headers=headers)
    except httpx.HTTPError as exc:
        return CheckResult("GitLab token", False, f"request failed: {exc.__class__.__name__}")

    if response.status_code == 200:
        data = response.json()
        username = data.get("username", "unknown-user")
        return CheckResult("GitLab token", True, f"valid for GitLab user '{username}'")

    if response.status_code in {401, 403}:
        return CheckResult("GitLab token", False, "invalid or insufficient permissions")

    return CheckResult("GitLab token", False, f"unexpected GitLab response HTTP {response.status_code}")


def check_vertex_ai_configuration() -> CheckResult:
    settings = get_settings()
    if not settings.gcp_project_id or not settings.gcp_location:
        return CheckResult("Vertex AI config", False, "GCP_PROJECT_ID or GCP_LOCATION is missing")

    try:
        from google.cloud import aiplatform

        aiplatform.init(project=settings.gcp_project_id, location=settings.gcp_location)
    except ImportError:
        return CheckResult("Vertex AI config", False, "google-cloud-aiplatform is not installed")
    except Exception as exc:
        return CheckResult("Vertex AI config", False, f"initialization failed: {exc.__class__.__name__}")

    return CheckResult(
        "Vertex AI config",
        True,
        f"initialized for project '{settings.gcp_project_id}' in '{settings.gcp_location}'",
    )


def check_google_credentials() -> CheckResult:
    try:
        import google.auth

        credentials, project_id = google.auth.default()
    except ImportError:
        return CheckResult("Google credentials", False, "google-auth is not installed")
    except Exception as exc:
        return CheckResult(
            "Google credentials",
            False,
            f"Application Default Credentials unavailable: {exc.__class__.__name__}",
        )

    if not credentials:
        return CheckResult("Google credentials", False, "Application Default Credentials unavailable")

    if project_id:
        return CheckResult("Google credentials", True, f"ADC found for project '{project_id}'")

    return CheckResult("Google credentials", True, "ADC found")


async def main() -> int:
    settings = get_settings()
    print("SyntaxSentinel environment verification")
    print("Secrets are checked but never printed.\n")

    print("Configuration")
    config_results = check_required_settings()
    for result in config_results:
        print_result(result)

    print("\nGitLab")
    print_result(CheckResult("GitLab base URL", bool(settings.gitlab_base_url), settings.gitlab_base_url))
    gitlab_result = await check_gitlab_token()
    print_result(gitlab_result)

    print("\nGoogle Cloud")
    vertex_result = check_vertex_ai_configuration()
    print_result(vertex_result)
    credentials_result = check_google_credentials()
    print_result(credentials_result)

    if settings.dry_run:
        print_warn("DRY_RUN", "enabled; write operations will be simulated in later sprints")

    all_results = [*config_results, gitlab_result, vertex_result, credentials_result]
    failed = [result for result in all_results if not result.ok]

    print("\nSummary")
    if failed:
        print(f"[FAIL] {len(failed)} check(s) failed. Fix the items above and run this script again.")
        return 1

    print("[OK] Environment is ready for SyntaxSentinel development.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
