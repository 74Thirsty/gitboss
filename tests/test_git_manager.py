def test_run_git_command_accepts_optional_git_prefix(tmp_path):
    repo = Repo.init(tmp_path)
    _commit_file(repo, tmp_path, "a.txt", "one\n", "init")

    manager = GitManager(tmp_path)
    output = manager.run_git_command("git status --short")

    assert isinstance(output, str)
from pathlib import Path

from git import Repo

from gitboss.core.git_manager import GitManager


def _commit_file(repo: Repo, path: Path, rel_name: str, content: str, message: str) -> None:
    file_path = path / rel_name
    file_path.write_text(content, encoding="utf-8")
    repo.index.add([rel_name])
    repo.index.commit(message)


def test_commit_listing_and_detail(tmp_path):
    repo = Repo.init(tmp_path)
    _commit_file(repo, tmp_path, "a.txt", "one\n", "init")
    _commit_file(repo, tmp_path, "a.txt", "one\ntwo\n", "update a")

    manager = GitManager(tmp_path)
    commits = manager.list_commits(limit=10)

    assert len(commits) == 2
    assert commits[0].subject == "update a"

    detail = manager.get_commit_details(commits[0].sha)
    assert detail.author_name
    assert detail.message.strip() == "update a"
    assert any(change.path == "a.txt" for change in detail.file_summaries)


def test_diff_stat_and_patch(tmp_path):
    repo = Repo.init(tmp_path)
    _commit_file(repo, tmp_path, "a.txt", "one\n", "init")
    _commit_file(repo, tmp_path, "a.txt", "one\ntwo\n", "update a")

    manager = GitManager(tmp_path)
    stat = manager.diff_stat("HEAD~1", "HEAD")
    patch = manager.diff_patch("HEAD~1", "HEAD")

    assert "a.txt" in stat
    assert "+two" in patch


def test_origin_repository_name_parsing(tmp_path):
    repo = Repo.init(tmp_path)
    repo.create_remote("origin", "git@github.com:octo/repo.git")

    manager = GitManager(tmp_path)
    assert manager.get_origin_repository_name() == "octo/repo"


def test_list_commits_with_all_flag(tmp_path):
    repo = Repo.init(tmp_path)
    _commit_file(repo, tmp_path, "a.txt", "one\n", "init")
    default_branch = repo.active_branch.name
    repo.create_head("feature").checkout()
    _commit_file(repo, tmp_path, "b.txt", "branch\n", "feature commit")
    repo.heads[default_branch].checkout()

    manager = GitManager(tmp_path)
    commits = manager.list_commits(limit=20, rev="--all")
    subjects = [commit.subject for commit in commits]
    assert "feature commit" in subjects


def test_list_commit_graph_returns_structured_rows(tmp_path):
    repo = Repo.init(tmp_path)
    _commit_file(repo, tmp_path, "a.txt", "one\n", "init")
    _commit_file(repo, tmp_path, "a.txt", "one\ntwo\n", "update a")

    manager = GitManager(tmp_path)
    rows = manager.list_commit_graph(limit=10, rev="HEAD")

    assert rows
    assert rows[0].sha
    assert rows[0].short_sha
    assert rows[0].subject



def test_clone_creates_missing_parent_directory(tmp_path):
    source_repo_path = tmp_path / "source"
    source_repo = Repo.init(source_repo_path)
    _commit_file(source_repo, source_repo_path, "README.md", "hello\n", "init")

    destination = tmp_path / "nested" / "target"
    cloned_path = GitManager.clone(str(source_repo_path), destination)

    assert cloned_path == destination
    assert (destination / ".git").exists()
