"""Utilities for discovering Git repositories on disk."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

LOGGER = logging.getLogger(__name__)


def is_git_repository(path: Path) -> bool:
    return (path / ".git").is_dir()


def scan_for_repositories(base_directory: Path, max_depth: int = 2) -> List[Path]:
    """Search for Git repositories within ``base_directory`` up to ``max_depth`` levels."""
    if not base_directory.exists():
        LOGGER.warning("Base directory %s does not exist", base_directory)
        return []

    repositories: List[Path] = []
    base_directory = base_directory.resolve()

    def _scan(directory: Path, depth: int) -> None:
        if depth > max_depth:
            return
        if is_git_repository(directory):
            repositories.append(directory)
            return
        for child in directory.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                _scan(child, depth + 1)

    _scan(base_directory, 0)
    return repositories


__all__ = ["scan_for_repositories", "is_git_repository"]
