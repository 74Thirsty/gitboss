"""Entry point for the GitBoss application."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

try:  # pragma: no cover - import guard
    from PyQt5.QtWidgets import QApplication
except ImportError as exc:  # pragma: no cover - import guard
    QApplication = None  # type: ignore[assignment]
    _QT_IMPORT_ERROR = exc
else:  # pragma: no cover - import guard
    _QT_IMPORT_ERROR = None

from typing import TYPE_CHECKING

from .core.logger import configure_logging
from .core.repository_scanner import scan_for_repositories
from .data.config_manager import AppConfig, load_config, save_config

if TYPE_CHECKING:  # pragma: no cover - import only for type checking
    from .ui.main_window import MainWindow
    from .ui.startup_wizard import StartupWizard

LOGGER = logging.getLogger(__name__)


class QtLogHandler(logging.Handler):
    """Log handler that forwards records to a callback."""

    def __init__(self, callback) -> None:
        super().__init__()
        self.callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        self.callback(message)


def _collect_repositories(config: AppConfig) -> list[Path]:
    stored = [Path(p) for p in config.preferences.get("repositories", [])]
    if config.base_directory:
        scanned = scan_for_repositories(Path(config.base_directory))
        # Merge stored and scanned repositories while preserving order.
        seen: set[Path] = set()
        merged: list[Path] = []
        for repo in stored + scanned:
            repo = repo.resolve()
            if repo not in seen:
                merged.append(repo)
                seen.add(repo)
        return merged
    return stored


def main() -> int:
    if QApplication is None:
        message = (
            "PyQt5 is required to run the GitBoss UI. Install the project dependencies "
            "with `pip install -r requirements.txt`."
        )
        if _QT_IMPORT_ERROR is not None:
            raise SystemExit(f"{message}\nOriginal error: {_QT_IMPORT_ERROR}")
        raise SystemExit(message)

    from .ui.startup_wizard import StartupWizard

    configure_logging()
    app = QApplication(sys.argv)

    config = load_config()
    if not StartupWizard.run_if_needed(config):
        LOGGER.info("Startup wizard cancelled. Exiting application.")
        return 0

    save_config(config)

    repositories = _collect_repositories(config)

    from .ui.main_window import MainWindow

    window = MainWindow(config, repositories)
    window.show()

    handler = QtLogHandler(lambda message: window.log_console.append(message))
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logging.getLogger().addHandler(handler)

    LOGGER.info("GitBoss started with %d repositories", len(repositories))

    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
