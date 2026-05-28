"""GitLab MCP-style tool client backed by the GitLab REST API v4.

The interface is intentionally tool-like so it can be replaced by an official
GitLab MCP server integration later without changing the orchestrator contract.
"""

import asyncio
import logging
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class GitLabAPIError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_data: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class GitLabAuthenticationError(GitLabAPIError):
    """Raised when GitLab rejects or cannot use the configured token."""


class GitLabNotFoundError(GitLabAPIError):
    """Raised when GitLab returns 404 for a requested resource."""


class GitLabRateLimitError(GitLabAPIError):
    """Raised when GitLab returns HTTP 429."""


class GitLabMCPClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 15.0,
        max_retries: int = 2,
    ) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.gitlab_base_url.rstrip("/")
        self.api_base_url = f"{self.base_url}/api/v4"
        self.timeout = timeout
        self.max_retries = max_retries
        self._external_client = http_client
        self._client: httpx.AsyncClient | None = http_client

    async def __aenter__(self) -> "GitLabMCPClient":
        self._get_client()
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._client is not None and self._external_client is None:
            await self._client.aclose()
        self._client = self._external_client

    async def list_pipeline_jobs(self, project_id: int, pipeline_id: int) -> list[dict[str, Any]]:
        response = await self._request_json(
            "GET",
            f"/projects/{project_id}/pipelines/{pipeline_id}/jobs",
            params={"include_retried": "true"},
        )
        if not isinstance(response, list):
            raise GitLabAPIError("GitLab returned an unexpected jobs payload")
        return response

    async def get_failed_jobs(self, project_id: int, pipeline_id: int) -> list[dict[str, Any]]:
        jobs = await self.list_pipeline_jobs(project_id, pipeline_id)
        return [job for job in jobs if job.get("status") == "failed"]

    async def read_job_trace(self, project_id: int, job_id: int) -> str:
        response = await self._request("GET", f"/projects/{project_id}/jobs/{job_id}/trace")
        return response.text

    async def get_file_content(self, project_id: int, file_path: str, ref: str) -> str:
        encoded_file_path = quote(file_path, safe="")
        response = await self._request(
            "GET",
            f"/projects/{project_id}/repository/files/{encoded_file_path}/raw",
            params={"ref": ref},
        )
        return response.text

    async def create_branch(self, project_id: int, branch_name: str, ref: str) -> dict[str, Any]:
        if self.settings.dry_run:
            logger.info(
                "Dry-run GitLab create_branch",
                extra={"project_id": project_id, "branch_name": branch_name, "ref": ref},
            )
            return {"dry_run": True, "name": branch_name, "ref": ref}

        return await self._request_json(
            "POST",
            f"/projects/{project_id}/repository/branches",
            json={"branch": branch_name, "ref": ref},
        )

    async def commit_file_changes(
        self,
        project_id: int,
        branch: str,
        commit_message: str,
        actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if self.settings.dry_run:
            logger.info(
                "Dry-run GitLab commit_file_changes",
                extra={"project_id": project_id, "branch": branch, "action_count": len(actions)},
            )
            return {
                "dry_run": True,
                "id": "dry-run-commit",
                "branch": branch,
                "message": commit_message,
                "action_count": len(actions),
            }

        return await self._request_json(
            "POST",
            f"/projects/{project_id}/repository/commits",
            json={
                "branch": branch,
                "commit_message": commit_message,
                "actions": actions,
            },
        )

    async def create_merge_request(
        self,
        project_id: int,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        if self.settings.dry_run:
            logger.info(
                "Dry-run GitLab create_merge_request",
                extra={
                    "project_id": project_id,
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "title": title,
                },
            )
            return {
                "dry_run": True,
                "iid": 0,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "labels": labels or [],
                "web_url": None,
            }

        payload: dict[str, Any] = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
            "remove_source_branch": False,
        }
        if labels:
            payload["labels"] = ",".join(labels)

        return await self._request_json(
            "POST",
            f"/projects/{project_id}/merge_requests",
            json=payload,
        )

    async def add_merge_request_note(self, project_id: int, mr_iid: int, body: str) -> dict[str, Any]:
        if self.settings.dry_run:
            logger.info(
                "Dry-run GitLab add_merge_request_note",
                extra={"project_id": project_id, "mr_iid": mr_iid},
            )
            return {"dry_run": True, "id": 0, "merge_request_iid": mr_iid, "body": body}

        return await self._request_json(
            "POST",
            f"/projects/{project_id}/merge_requests/{mr_iid}/notes",
            json={"body": body},
        )

    async def get_project(self, project_id: int) -> dict[str, Any]:
        response = await self._request_json("GET", f"/projects/{project_id}")
        if not isinstance(response, dict):
            raise GitLabAPIError("GitLab returned an unexpected project payload")
        return response

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers={"PRIVATE-TOKEN": self.settings.gitlab_personal_access_token},
                timeout=self.timeout,
            )
        return self._client

    async def _request_json(self, method: str, path: str, **kwargs: Any) -> Any:
        response = await self._request(method, path, **kwargs)
        try:
            return response.json()
        except ValueError as exc:
            raise GitLabAPIError("GitLab returned invalid JSON", status_code=response.status_code) from exc

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        if not self.settings.gitlab_personal_access_token:
            raise GitLabAuthenticationError("GitLab token is not configured")

        client = self._get_client()
        last_error: GitLabAPIError | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await client.request(method, path, **kwargs)
            except httpx.TimeoutException as exc:
                last_error = GitLabAPIError("GitLab request timed out")
                if attempt >= self.max_retries:
                    raise last_error from exc
                await asyncio.sleep(self._retry_delay(attempt))
                continue
            except httpx.TransportError as exc:
                last_error = GitLabAPIError(f"GitLab transport error: {exc.__class__.__name__}")
                if attempt >= self.max_retries:
                    raise last_error from exc
                await asyncio.sleep(self._retry_delay(attempt))
                continue

            if response.status_code >= 500 and attempt < self.max_retries:
                logger.warning(
                    "Retrying GitLab request after server error",
                    extra={"method": method, "path": path, "status_code": response.status_code},
                )
                await asyncio.sleep(self._retry_delay(attempt))
                continue

            self._raise_for_status(response)
            return response

        if last_error is not None:
            raise last_error
        raise GitLabAPIError("GitLab request failed after retries")

    def _raise_for_status(self, response: httpx.Response) -> None:
        if 200 <= response.status_code < 300:
            return

        response_data = self._safe_response_data(response)
        message = self._extract_error_message(response_data) or f"GitLab API error HTTP {response.status_code}"

        if response.status_code in {401, 403}:
            raise GitLabAuthenticationError(message, status_code=response.status_code, response_data=response_data)
        if response.status_code == 404:
            raise GitLabNotFoundError(message, status_code=response.status_code, response_data=response_data)
        if response.status_code == 429:
            raise GitLabRateLimitError(message, status_code=response.status_code, response_data=response_data)

        raise GitLabAPIError(message, status_code=response.status_code, response_data=response_data)

    @staticmethod
    def _safe_response_data(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    @staticmethod
    def _extract_error_message(response_data: Any) -> str | None:
        if isinstance(response_data, dict):
            message = response_data.get("message") or response_data.get("error")
            if isinstance(message, str):
                return message
            if isinstance(message, dict):
                return str(message)
        if isinstance(response_data, str):
            return response_data.strip() or None
        return None

    @staticmethod
    def _retry_delay(attempt: int) -> float:
        return 0.25 * (attempt + 1)
