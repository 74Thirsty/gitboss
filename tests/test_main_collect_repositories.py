from pathlib import Path

from gitboss.data.config_manager import AppConfig
from gitboss.main import _collect_repositories


def test_collect_repositories_merges_and_deduplicates(tmp_path):
    base = tmp_path
    stored_repo = base / "stored"
    scanned_repo = base / "scanned"

    for repo in (stored_repo, scanned_repo):
        (repo / ".git").mkdir(parents=True)

    config = AppConfig()
    config.base_directory = str(base)
    config.preferences["repositories"] = [str(stored_repo)]

    result = _collect_repositories(config)

    assert result[0] == stored_repo.resolve()
    assert scanned_repo.resolve() in result
    # Ensure duplicates removed
    assert len(result) == 2


def test_collect_repositories_without_base_directory():
    config = AppConfig()
    config.preferences["repositories"] = ["/tmp/example"]

    result = _collect_repositories(config)

    assert result == [Path("/tmp/example").resolve()]
