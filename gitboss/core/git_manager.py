"""Core Git management utilities backed by GitPython."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional

from git import Repo, InvalidGitRepositoryError, GitCommandError

LOGGER = logging.getLogger(__name__)


class GitManager:
    """Wrapper around :class:`git.Repo` providing higher level helpers."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = Path(repo_path)
        self.repo: Optional[Repo] = None

    def load(self) -> None:
        try:
            self.repo = Repo(self.repo_path)
        except InvalidGitRepositoryError as exc:
            LOGGER.error("Invalid git repository at %s", self.repo_path)
            raise ValueError(f"Invalid git repository: {self.repo_path}") from exc

    def is_dirty(self) -> bool:
        if not self.repo:
            self.load()
        assert self.repo is not None
        return self.repo.is_dirty(untracked_files=True)

    def list_branches(self) -> List[str]:
        if not self.repo:
            self.load()
        assert self.repo is not None
        return [branch.name for branch in self.repo.branches]

    def current_branch(self) -> str:
        if not self.repo:
            self.load()
        assert self.repo is not None
        return self.repo.active_branch.name

    def list_status(self) -> Iterable[str]:
        if not self.repo:
            self.load()
        assert self.repo is not None
        try:
            return self.repo.git.status(porcelain=True).splitlines()
        except GitCommandError as exc:
            LOGGER.error("Failed to retrieve status: %s", exc)
            return []

    def pull(self, remote_name: str = "origin", branch: Optional[str] = None) -> str:
        if not self.repo:
            self.load()
        assert self.repo is not None
        remote = self.repo.remote(remote_name)
        branch = branch or self.current_branch()
        result = remote.pull(branch)
        LOGGER.info("Pulled %s/%s", remote_name, branch)
        return "\n".join(map(str, result))

    def fetch(self, remote_name: str = "origin") -> str:
        if not self.repo:
            self.load()
        assert self.repo is not None
        remote = self.repo.remote(remote_name)
        result = remote.fetch()
        LOGGER.info("Fetched from %s", remote_name)
        return "\n".join(map(str, result))

    def push(self, remote_name: str = "origin", branch: Optional[str] = None) -> str:
        if not self.repo:
            self.load()
        assert self.repo is not None
        branch = branch or self.current_branch()
        remote = self.repo.remote(remote_name)
        result = remote.push(branch)
        LOGGER.info("Pushed %s to %s/%s", branch, remote_name, branch)
        return "\n".join(map(str, result))


__all__ = ["GitManager"]
