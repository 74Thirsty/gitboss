from gitboss.core.repository_scanner import scan_for_repositories


def test_scan_for_repositories_discovers_git_directories(tmp_path):
    repo_a = tmp_path / "repo_a"
    repo_a_git = repo_a / ".git"
    repo_a_git.mkdir(parents=True)

    nested = tmp_path / "nested"
    nested_repo = nested / "repo_nested"
    (nested_repo / ".git").mkdir(parents=True)

    (tmp_path / "not_a_repo").mkdir()

    discovered = scan_for_repositories(tmp_path, max_depth=2)

    resolved = {path.resolve() for path in discovered}
    assert repo_a.resolve() in resolved
    assert nested_repo.resolve() in resolved
    assert len(resolved) == 2


def test_scan_for_repositories_handles_missing_directory(tmp_path):
    missing = tmp_path / "missing"
    assert scan_for_repositories(missing) == []
