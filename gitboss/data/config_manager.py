"""Configuration management for GitBoss."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path(os.path.expanduser("~/.config/gitboss"))
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    """Simple container for application configuration."""

    base_directory: str = ""
    auto_fetch_interval: int = 15
    default_theme: str = "dark"
    last_active_repo: str = ""
    git_user_name: str = ""
    git_user_email: str = ""
    preferences: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_directory": self.base_directory,
            "auto_fetch_interval": self.auto_fetch_interval,
            "default_theme": self.default_theme,
            "last_active_repo": self.last_active_repo,
            "git_user_name": self.git_user_name,
            "git_user_email": self.git_user_email,
            "preferences": self.preferences,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        return cls(
            base_directory=data.get("base_directory", ""),
            auto_fetch_interval=int(data.get("auto_fetch_interval", 15)),
            default_theme=data.get("default_theme", "dark"),
            last_active_repo=data.get("last_active_repo", ""),
            git_user_name=data.get("git_user_name", ""),
            git_user_email=data.get("git_user_email", ""),
            preferences=data.get("preferences", {}),
        )


def ensure_config_directory() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    ensure_config_directory()
    if not CONFIG_FILE.exists():
        return AppConfig()

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        # If the file is corrupted, reset to defaults but keep a backup.
        corrupted_path = CONFIG_FILE.with_suffix(".corrupted")
        try:
            CONFIG_FILE.rename(corrupted_path)
        except OSError:
            pass
        return AppConfig()

    return AppConfig.from_dict(data)


def save_config(config: AppConfig) -> None:
    ensure_config_directory()
    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(config.to_dict(), file, indent=2)


__all__ = [
    "AppConfig",
    "load_config",
    "save_config",
    "CONFIG_FILE",
]
