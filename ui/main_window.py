"""Main application window for GitBoss."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAction,
    QDockWidget,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from core.git_manager import GitManager
from data.config_manager import AppConfig, save_config

LOGGER = logging.getLogger(__name__)


class RepositoryListWidget(QListWidget):
    """Widget listing repositories discovered on disk."""

    def populate(self, repos: Iterable[Path]) -> None:
        self.clear()
        for repo in repos:
            item = QListWidgetItem(str(repo))
            item.setData(Qt.UserRole, str(repo))
            self.addItem(item)


class LogConsole(QTextEdit):
    """Read-only widget for displaying log output."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        font = QFont("Fira Code", 10)
        self.setFont(font)

    def append_lines(self, lines: Iterable[str]) -> None:
        self.append("\n".join(lines))


class MainWindow(QMainWindow):
    """Primary UI for GitBoss."""

    def __init__(self, config: AppConfig, repos: List[Path]) -> None:
        super().__init__()
        self.config = config
        self.repos = repos
        self.current_repo: Path | None = None

        self.setWindowTitle("GitBoss")
        self.resize(1200, 800)

        self.repo_list_widget = RepositoryListWidget()
        self.repo_list_widget.populate(self.repos)
        self.repo_list_widget.currentItemChanged.connect(self._on_repo_selected)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self._create_dashboard_tab(), "Dashboard")
        self.tab_widget.addTab(self._create_placeholder_tab("Commits"), "Commits")
        self.tab_widget.addTab(self._create_placeholder_tab("Diffs"), "Diffs")
        self.tab_widget.addTab(self._create_placeholder_tab("Issues"), "Issues")
        self.tab_widget.addTab(self._create_placeholder_tab("Pull Requests"), "PRs")
        self.tab_widget.addTab(self._create_placeholder_tab("Settings"), "Settings")

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(QLabel("Repositories"))
        layout.addWidget(self.repo_list_widget)
        layout.addWidget(self.tab_widget, stretch=1)
        self.setCentralWidget(central_widget)

        self.log_console = LogConsole()
        log_dock = QDockWidget("Command Log", self)
        log_dock.setWidget(self.log_console)
        log_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self._create_menus()
        if repos:
            self.repo_list_widget.setCurrentRow(0)

    def _create_dashboard_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.repo_status_label = QLabel("Select a repository to view details.")
        self.repo_status_label.setWordWrap(True)
        layout.addWidget(self.repo_status_label)
        return widget

    def _create_placeholder_tab(self, name: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(f"{name} view coming soon."))
        layout.addStretch(1)
        return widget

    def _create_menus(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        file_menu = self.menuBar().addMenu("File")

        add_repo_action = QAction("Add Existing Repo", self)
        add_repo_action.triggered.connect(self._on_add_repo)
        file_menu.addAction(add_repo_action)
        toolbar.addAction(add_repo_action)

        clone_repo_action = QAction("Clone Repo", self)
        clone_repo_action.triggered.connect(self._on_clone_repo)
        file_menu.addAction(clone_repo_action)
        toolbar.addAction(clone_repo_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _on_repo_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            self.current_repo = None
            self.repo_status_label.setText("No repository selected.")
            return
        self.current_repo = Path(current.data(Qt.UserRole))
        self.status_bar.showMessage(f"Selected repository: {self.current_repo}")
        try:
            manager = GitManager(self.current_repo)
            dirty = manager.is_dirty()
            branches = ", ".join(manager.list_branches())
            status_lines = manager.list_status()
        except ValueError as exc:
            QMessageBox.critical(self, "Repository Error", str(exc))
            LOGGER.exception("Failed to load repository")
            return

        details = [
            f"Path: {self.current_repo}",
            f"Branches: {branches or 'None'}",
            "Working Tree: Dirty" if dirty else "Working Tree: Clean",
        ]
        if status_lines:
            details.append("\n".join(status_lines))
        self.repo_status_label.setText("\n".join(details))

    def _on_add_repo(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Repository Directory", self.config.base_directory)
        if not directory:
            return
        path = Path(directory)
        if path not in self.repos:
            self.repos.append(path)
            self.repo_list_widget.populate(self.repos)
            self.repo_list_widget.setCurrentRow(self.repos.index(path))
            LOGGER.info("Added repository: %s", path)
            self._persist_repositories()

    def _on_clone_repo(self) -> None:
        QMessageBox.information(self, "Clone Repository", "Clone functionality will be available soon.")

    def _persist_repositories(self) -> None:
        self.config.preferences["repositories"] = [str(repo) for repo in self.repos]
        save_config(self.config)


__all__ = ["MainWindow"]
