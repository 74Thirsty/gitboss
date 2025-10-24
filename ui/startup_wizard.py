"""Startup wizard for initial configuration."""
from __future__ import annotations

import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from data.config_manager import AppConfig, save_config

LOGGER = logging.getLogger(__name__)


class StartupWizard(QDialog):
    """Guides the user through initial setup of GitBoss."""

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Welcome to GitBoss")
        self.resize(400, 200)

        layout = QVBoxLayout(self)
        self.info_label = QLabel(
            "Select a base directory to scan for Git repositories."
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.select_button = QPushButton("Choose Directory")
        self.select_button.clicked.connect(self._choose_directory)
        layout.addWidget(self.select_button)

        self.continue_button = QPushButton("Continue")
        self.continue_button.clicked.connect(self.accept)
        self.continue_button.setEnabled(bool(self.config.base_directory))
        layout.addWidget(self.continue_button)

    def _choose_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Base Directory", self.config.base_directory)
        if not directory:
            return
        self.config.base_directory = directory
        save_config(self.config)
        LOGGER.info("Base directory set to %s", directory)
        self.continue_button.setEnabled(True)

    @staticmethod
    def run_if_needed(config: AppConfig, parent=None) -> bool:
        if config.base_directory:
            return True
        dialog = StartupWizard(config, parent)
        return dialog.exec() == QDialog.Accepted


__all__ = ["StartupWizard"]
