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
