"""GitHub API integration helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from github import Github, GithubException

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowSummary:
    """Lightweight view over a GitHub Actions workflow."""

    id: int
    name: str
    path: str
    state: str


@dataclass(frozen=True)
class WorkflowRunSummary:
    """Lightweight view over a workflow run."""

    id: int
    name: str
    status: str | None
    conclusion: str | None
    html_url: str
    event: str
    head_branch: str | None
    head_sha: str


@dataclass(frozen=True)
class WorkflowArtifactSummary:
    """Lightweight view over a workflow artifact."""

    id: int
    name: str
    size_in_bytes: int
    archive_download_url: str
    expired: bool


class GitHubManager:
    """Wrapper around the PyGithub client with GitHub Actions support."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token
        self.client: Github | None = None

    def authenticate(self, token: str | None = None) -> None:
        self.token = token or self.token
        if not self.token:
            raise ValueError("GitHub token is required")
        self.client = Github(self.token)
        LOGGER.info("Authenticated with GitHub")

    def _require_client(self) -> Github:
        if not self.client:
            raise RuntimeError("GitHub client is not authenticated")
        return self.client

    def _get_repository(self, full_name: str):
        try:
            return self._require_client().get_repo(full_name)
        except GithubException as exc:
            LOGGER.error("Failed to access repository %s: %s", full_name, exc)
            raise

    def list_repositories(self) -> List[str]:
        try:
            return [repo.full_name for repo in self._require_client().get_user().get_repos()]
        except GithubException as exc:
            LOGGER.error("Failed to fetch repositories: %s", exc)
            raise

    def list_workflows(self, repository: str) -> List[WorkflowSummary]:
        """List GitHub Actions workflows for a repository."""

        try:
            workflows = self._get_repository(repository).get_workflows()
            return [
                WorkflowSummary(
                    id=workflow.id,
                    name=workflow.name,
                    path=workflow.path,
                    state=workflow.state,
                )
                for workflow in workflows
            ]
        except GithubException as exc:
            LOGGER.error("Failed to list workflows for %s: %s", repository, exc)
            raise

    def list_workflow_runs(
        self,
        repository: str,
        workflow_id: int,
        *,
        branch: str | None = None,
        event: str | None = None,
        status: str | None = None,
    ) -> List[WorkflowRunSummary]:
        """List workflow runs for the selected workflow."""

        params: Dict[str, Any] = {}
        if branch:
            params["branch"] = branch
        if event:
            params["event"] = event
        if status:
            params["status"] = status

        try:
            workflow = self._get_repository(repository).get_workflow(workflow_id)
            runs = workflow.get_runs(**params)
            return [
                WorkflowRunSummary(
                    id=run.id,
                    name=run.name,
                    status=run.status,
                    conclusion=run.conclusion,
                    html_url=run.html_url,
                    event=run.event,
                    head_branch=run.head_branch,
                    head_sha=run.head_sha,
                )
                for run in runs
            ]
        except GithubException as exc:
            LOGGER.error(
                "Failed to list workflow runs for %s workflow %s: %s",
                repository,
                workflow_id,
                exc,
            )
            raise

    def dispatch_workflow(
        self,
        repository: str,
        workflow_id: int,
        *,
        ref: str,
        inputs: Dict[str, Any] | None = None,
    ) -> bool:
        """Trigger a workflow_dispatch event."""

        try:
            workflow = self._get_repository(repository).get_workflow(workflow_id)
            return workflow.create_dispatch(ref=ref, inputs=inputs or {})
        except GithubException as exc:
            LOGGER.error(
                "Failed to dispatch workflow %s for %s at ref %s: %s",
                workflow_id,
                repository,
                ref,
                exc,
            )
            raise

    def rerun_workflow(self, repository: str, run_id: int) -> bool:
        """Re-run a workflow run."""

        try:
            run = self._get_repository(repository).get_workflow_run(run_id)
            return run.rerun()
        except GithubException as exc:
            LOGGER.error("Failed to rerun workflow run %s for %s: %s", run_id, repository, exc)
            raise

    def cancel_workflow(self, repository: str, run_id: int) -> bool:
        """Cancel a workflow run."""

        try:
            run = self._get_repository(repository).get_workflow_run(run_id)
            return run.cancel()
        except GithubException as exc:
            LOGGER.error("Failed to cancel workflow run %s for %s: %s", run_id, repository, exc)
            raise

    def get_workflow_logs_url(self, repository: str, run_id: int) -> str:
        """Return URL to the zipped logs archive for a workflow run."""

        try:
            run = self._get_repository(repository).get_workflow_run(run_id)
            return run.logs_url()
        except GithubException as exc:
            LOGGER.error("Failed to get workflow logs URL for run %s in %s: %s", run_id, repository, exc)
            raise

    def list_workflow_artifacts(self, repository: str, run_id: int) -> List[WorkflowArtifactSummary]:
        """List build artifacts emitted by a workflow run."""

        try:
            run = self._get_repository(repository).get_workflow_run(run_id)
            artifacts = run.get_artifacts()
            return [
                WorkflowArtifactSummary(
                    id=artifact.id,
                    name=artifact.name,
                    size_in_bytes=artifact.size_in_bytes,
                    archive_download_url=artifact.archive_download_url,
                    expired=artifact.expired,
                )
                for artifact in artifacts
            ]
        except GithubException as exc:
            LOGGER.error("Failed to list artifacts for run %s in %s: %s", run_id, repository, exc)
            raise


__all__ = [
    "GitHubManager",
    "WorkflowArtifactSummary",
    "WorkflowRunSummary",
    "WorkflowSummary",
]
