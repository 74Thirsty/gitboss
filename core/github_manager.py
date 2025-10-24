"""GitHub API integration helpers."""
from __future__ import annotations

import logging
from typing import List

from github import Github, GithubException

LOGGER = logging.getLogger(__name__)


class GitHubManager:
    """Lightweight wrapper around the PyGithub client."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token
        self.client: Github | None = None

    def authenticate(self, token: str | None = None) -> None:
        self.token = token or self.token
        if not self.token:
            raise ValueError("GitHub token is required")
        self.client = Github(self.token)
        LOGGER.info("Authenticated with GitHub")

    def list_repositories(self) -> List[str]:
        if not self.client:
            raise RuntimeError("GitHub client is not authenticated")
        try:
            return [repo.full_name for repo in self.client.get_user().get_repos()]
        except GithubException as exc:
            LOGGER.error("Failed to fetch repositories: %s", exc)
            raise


__all__ = ["GitHubManager"]
