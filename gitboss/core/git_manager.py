"""Core Git management utilities backed by GitPython."""
from __future__ import annotations

import logging
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

from git import GitCommandError, InvalidGitRepositoryError, Repo

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class GitFileChangeSummary:
    """Summary of one file changed in a commit."""

    path: str
    insertions: int
    deletions: int
    change_type: str


@dataclass(frozen=True)
class GitCommitSummary:
    """Compact commit summary for list rendering."""

    sha: str
    short_sha: str
    subject: str
    author_name: str
    authored_datetime: str


@dataclass(frozen=True)
class GitCommitDetail:
    """Detailed commit data for deep inspection."""

    sha: str
    author_name: str
    author_email: str
    authored_datetime: str
    message: str
    parents: list[str]
    file_summaries: list[GitFileChangeSummary]


@dataclass(frozen=True)
class GitGraphCommit:
    """One line of graph-rendered commit data."""
    graph_prefix: str
    sha: str
    short_sha: str
    refs: str
    author_name: str
    authored_date: str
    subject: str


class GitManager:
    """Wrapper around :class:`git.Repo` providing higher level helpers."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = Path(repo_path)
        self.repo: Optional[Repo] = None

    def load(self) -> None:
        try:
            self.repo = Repo(self.repo_path)
            self._ensure_safe_directory_configured()
        except InvalidGitRepositoryError as exc:
            LOGGER.error("Invalid git repository at %s", self.repo_path)
            raise ValueError(f"Invalid git repository: {self.repo_path}") from exc

    def _ensure_safe_directory_configured(self) -> None:
        """Ensure Git trusts this repository path to avoid dubious ownership failures."""
        repo_path = str(self.repo_path.resolve())
        try:
            result = subprocess.run(
                ["git", "config", "--global", "--get-all", "safe.directory"],
                check=False,
                capture_output=True,
                text=True,
            )
            configured = {line.strip() for line in result.stdout.splitlines() if line.strip()}
            if repo_path in configured:
                return
            subprocess.run(
                ["git", "config", "--global", "--add", "safe.directory", repo_path],
                check=True,
                capture_output=True,
                text=True,
            )
            LOGGER.info("Added safe.directory for %s", repo_path)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Unable to update git safe.directory for %s: %s", repo_path, exc)

    def _require_repo(self) -> Repo:
        if not self.repo:
            self.load()
        assert self.repo is not None
        return self.repo

    def is_dirty(self) -> bool:
        return self._require_repo().is_dirty(untracked_files=True)

    def list_branches(self) -> List[str]:
        return [branch.name for branch in self._require_repo().branches]

    def current_branch(self) -> str:
        return self._require_repo().active_branch.name

    def list_status(self) -> Iterable[str]:
        try:
            return self._require_repo().git.status(porcelain=True).splitlines()
        except GitCommandError as exc:
            LOGGER.error("Failed to retrieve status: %s", exc)
            return []

    def list_branch_refs(self) -> list[str]:
        repo = self._require_repo()
        output = repo.git.branch("--all", "--format=%(refname:short)")
        refs = [line.strip() for line in output.splitlines() if line.strip()]
        return sorted(dict.fromkeys(refs))

    def list_commits(self, limit: int = 200, rev: str = "HEAD") -> list[GitCommitSummary]:
        repo = self._require_repo()
        commits: list[GitCommitSummary] = []
        if rev == "--all":
            rev_arg = "--all"
        else:
            rev_arg = rev
        for commit in repo.iter_commits(rev_arg, max_count=limit):
            commits.append(
                GitCommitSummary(
                    sha=commit.hexsha,
                    short_sha=commit.hexsha[:10],
                    subject=commit.summary.decode() if isinstance(commit.summary, bytes) else commit.summary,
                    author_name=commit.author.name or "",
                    authored_datetime=commit.authored_datetime.isoformat(),
                )
            )
        return commits

    def render_commit_graph(self, limit: int = 200, rev: str = "HEAD") -> str:
        repo = self._require_repo()
        args = ["--graph", "--decorate", "--oneline", f"-n{limit}"]
        if rev == "--all":
            args.append("--all")
        else:
            args.append(rev)
        return repo.git.log(*args)

    def list_commit_graph(self, limit: int = 200, rev: str = "HEAD") -> list[GitGraphCommit]:
        """Return structured, graph-aligned commit rows for UI rendering."""
        repo = self._require_repo()
        pretty = "%x1f%H%x1f%h%x1f%d%x1f%an%x1f%ad%x1f%s"
        args = ["--graph", "--decorate=short", "--date=short", f"--pretty=format:{pretty}", f"-n{limit}"]
        if rev == "--all":
            args.append("--all")
        else:
            args.append(rev)
        output = repo.git.log(*args)
        rows: list[GitGraphCommit] = []
        for line in output.splitlines():
            if "\x1f" not in line:
                continue
            graph_prefix, payload = line.split("\x1f", 1)
            parts = payload.split("\x1f")
            if len(parts) != 6:
                continue
            sha, short_sha, refs, author_name, authored_date, subject = parts
            rows.append(
                GitGraphCommit(
                    graph_prefix=graph_prefix.rstrip(),
                    sha=sha,
                    short_sha=short_sha,
                    refs=refs.strip().strip("()"),
                    author_name=author_name,
                    authored_date=authored_date,
                    subject=subject,
                )
            )
        return rows

    def get_origin_repository_name(self) -> str | None:
        repo = self._require_repo()
        try:
            remote_url = repo.remote("origin").url
        except ValueError:
            return None
        if remote_url.startswith("git@"):
            _, path = remote_url.split(":", 1)
        else:
            parsed = urlparse(remote_url)
            path = parsed.path.lstrip("/")
        normalized = path.removesuffix(".git").strip("/")
        if normalized.count("/") < 1:
            return None
        owner, repo_name = normalized.split("/", 1)
        if not owner or not repo_name:
            return None
        return f"{owner}/{repo_name}"

    def get_commit_details(self, commit_sha: str) -> GitCommitDetail:
        repo = self._require_repo()
        commit = repo.commit(commit_sha)
        stats = commit.stats.files
        file_summaries: list[GitFileChangeSummary] = []
        for path, file_stats in stats.items():
            file_summaries.append(
                GitFileChangeSummary(
                    path=str(path),
                    insertions=int(file_stats.get("insertions", 0)),
                    deletions=int(file_stats.get("deletions", 0)),
                    change_type=str(file_stats.get("change_type", "modified")),
                )
            )
        return GitCommitDetail(
            sha=commit.hexsha,
            author_name=commit.author.name or "",
            author_email=commit.author.email or "",
            authored_datetime=commit.authored_datetime.isoformat(),
            message=commit.message.decode() if isinstance(commit.message, bytes) else commit.message,
            parents=[parent.hexsha for parent in commit.parents],
            file_summaries=file_summaries,
        )

    def diff_stat(self, base_ref: str, target_ref: str) -> str:
        try:
            return self._require_repo().git.diff("--stat", base_ref, target_ref)
        except GitCommandError as exc:
            raise ValueError(f"Failed to compute diff stat for {base_ref}..{target_ref}: {exc}") from exc

    def diff_patch(self, base_ref: str, target_ref: str) -> str:
        try:
            return self._require_repo().git.diff(base_ref, target_ref)
        except GitCommandError as exc:
            raise ValueError(f"Failed to compute patch for {base_ref}..{target_ref}: {exc}") from exc

    def pull(self, remote_name: str = "origin", branch: Optional[str] = None) -> str:
        repo = self._require_repo()
        remote = repo.remote(remote_name)
        branch = branch or self.current_branch()
        result = remote.pull(branch)
        LOGGER.info("Pulled %s/%s", remote_name, branch)
        return "\n".join(map(str, result))

    def fetch(self, remote_name: str = "origin") -> str:
        repo = self._require_repo()
        remote = repo.remote(remote_name)
        result = remote.fetch()
        LOGGER.info("Fetched from %s", remote_name)
        return "\n".join(map(str, result))

    def push(self, remote_name: str = "origin", branch: Optional[str] = None) -> str:
        repo = self._require_repo()
        branch = branch or self.current_branch()
        remote = repo.remote(remote_name)
        result = remote.push(branch)
        LOGGER.info("Pushed %s to %s/%s", branch, remote_name, branch)
        return "\n".join(map(str, result))

    @staticmethod
    def clone(repository_url: str, destination: Path) -> Path:
        destination = Path(destination)
        Repo.clone_from(repository_url, destination)
        LOGGER.info("Cloned %s into %s", repository_url, destination)
        return destination

    def create_branch(self, branch_name: str, checkout: bool = True) -> str:
        if not self.repo:
            self.load()
        assert self.repo is not None
        branch = self.repo.create_head(branch_name)
        if checkout:
            branch.checkout()
        LOGGER.info("Created branch %s (checkout=%s)", branch_name, checkout)
        return branch.name

    def run_git_command(self, command: str) -> str:
        """Run an arbitrary git command in this repository.

        Example inputs:
            - "status --short"
            - "rebase -i HEAD~5"
            - "checkout main"
        """

        if not self.repo:
            self.load()
        assert self.repo is not None

        argv = shlex.split(command)
        if not argv:
            raise ValueError("Git command cannot be empty")

        method = argv[0].replace("-", "_")
        args = argv[1:]
        try:
            git_callable = getattr(self.repo.git, method)
        except AttributeError as exc:
            raise ValueError(f"Unsupported git command: {argv[0]}") from exc

        try:
            output = git_callable(*args)
        except GitCommandError as exc:
            LOGGER.error("Git command failed (%s): %s", command, exc)
            raise

        LOGGER.info("Ran git command in %s: git %s", self.repo_path, command)
        return output or "(no output)"


__all__ = [
    "GitCommitDetail",
    "GitCommitSummary",
    "GitFileChangeSummary",
    "GitGraphCommit",
    "GitManager",
]
