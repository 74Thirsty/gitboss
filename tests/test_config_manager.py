from pathlib import Path

import pytest

from gitboss.data import config_manager
from gitboss.data.config_manager import AppConfig, load_config, save_config


def _patch_config_paths(monkeypatch: pytest.MonkeyPatch, directory: Path) -> None:
    config_dir = directory / "config"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(config_manager, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config_manager, "CONFIG_FILE", config_file)


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    _patch_config_paths(monkeypatch, tmp_path)

    config = AppConfig(
        base_directory=str(tmp_path),
        auto_fetch_interval=10,
        default_theme="light",
        last_active_repo="/tmp/repo",
        git_user_name="Example User",
        git_user_email="user@example.com",
        preferences={"repositories": ["/tmp/repo"]},
    )

    save_config(config)
    loaded = load_config()

    assert loaded == config


def test_load_config_resets_on_corruption(tmp_path, monkeypatch):
    _patch_config_paths(monkeypatch, tmp_path)

    config_dir = config_manager.CONFIG_DIR
    config_dir.mkdir(parents=True)
    config_file = config_manager.CONFIG_FILE
    config_file.write_text("not-json", encoding="utf-8")

    loaded = load_config()

    assert loaded == AppConfig()
    backup = config_file.with_suffix(".corrupted")
    assert backup.exists()
