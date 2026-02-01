"""Main application window for GitBoss."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDockWidget,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core.git_manager import GitManager
from ..core.repository_scanner import scan_for_repositories
from ..data.config_manager import AppConfig, save_config

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
        self._apply_theme()

        self.repo_list_widget = RepositoryListWidget()
        self.repo_list_widget.populate(self.repos)
        self.repo_list_widget.currentItemChanged.connect(self._on_repo_selected)

        self.repo_filter = QLineEdit()
        self.repo_filter.setPlaceholderText("Filter repositories...")
        self.repo_filter.textChanged.connect(self._filter_repositories)

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
        layout = QHBoxLayout(central_widget)

        repo_panel = QWidget()
        repo_layout = QVBoxLayout(repo_panel)
        repo_layout.addWidget(QLabel("Repositories"))
        repo_layout.addWidget(self.repo_filter)
        repo_layout.addWidget(self.repo_list_widget, stretch=1)
        repo_layout.addLayout(self._create_repo_actions())

        content_panel = QWidget()
        content_layout = QVBoxLayout(content_panel)
        content_layout.addWidget(self._create_header_widget())
        content_layout.addWidget(self.tab_widget, stretch=1)

        layout.addWidget(repo_panel, stretch=1)
        layout.addWidget(content_panel, stretch=3)
        self.setCentralWidget(central_widget)

        self.log_console = LogConsole()
        log_dock = QDockWidget("Command Log", self)
        log_dock.setWidget(self.log_console)
        log_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)
        self.log_dock = QDockWidget("Command Log", self)
        self.log_dock.setWidget(self.log_console)
        self.log_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)

        self.activity_list = QListWidget()
        self.activity_dock = QDockWidget("Activity Feed", self)
        self.activity_dock.setWidget(self.activity_list)
        self.activity_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.activity_dock)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self._create_menus()
        self._set_repo_actions_enabled(False)
        if repos:
            self.repo_list_widget.setCurrentRow(0)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #0f1115;
                color: #e6e6e6;
            }
            QLabel {
                color: #e6e6e6;
            }
            QLineEdit {
                background-color: #1a1e24;
                border: 1px solid #2a2f3a;
                border-radius: 6px;
                padding: 6px 8px;
                color: #e6e6e6;
            }
            QListWidget, QTextEdit {
                background-color: #151820;
                border: 1px solid #2a2f3a;
                border-radius: 8px;
                padding: 6px;
                color: #e6e6e6;
            }
            QPushButton {
                background-color: #2d6cdf;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #3b7bff;
            }
            QPushButton:disabled {
                background-color: #3b3f4a;
                color: #9aa0aa;
            }
            QTabWidget::pane {
                border: 1px solid #2a2f3a;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #151820;
                padding: 8px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #232935;
            }
            QFrame[card="true"] {
                background-color: #151820;
                border: 1px solid #2a2f3a;
                border-radius: 10px;
            }
            """
        )

    def _create_repo_actions(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self.add_repo_button = QPushButton("Add Repo")
        self.add_repo_button.clicked.connect(self._on_add_repo)
        self.rescan_button = QPushButton("Rescan")
        self.rescan_button.clicked.connect(self._on_rescan_repositories)
        layout.addWidget(self.add_repo_button)
        layout.addWidget(self.rescan_button)
        return layout

    def _create_header_widget(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        self.repo_title_label = QLabel("Select a repository to begin.")
        self.repo_title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self.repo_title_label, stretch=1)

        self.open_button = QPushButton("Open Folder")
        self.open_button.clicked.connect(self._open_in_file_manager)
        self.copy_button = QPushButton("Copy Path")
        self.copy_button.clicked.connect(self._copy_repo_path)
        self.refresh_button = QPushButton("Refresh Status")
        self.refresh_button.clicked.connect(self._refresh_current_repo)
        layout.addWidget(self.open_button)
        layout.addWidget(self.copy_button)
        layout.addWidget(self.refresh_button)
        return widget

    def _create_dashboard_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        stats_layout = QHBoxLayout()
        self.branch_card, self.branch_value_label = self._create_stat_card("Branches", "—")
        self.status_card, self.status_value_label = self._create_stat_card("Working Tree", "—")
        self.modified_card, self.modified_value_label = self._create_stat_card("Modified Files", "—")
        stats_layout.addWidget(self.branch_card)
        stats_layout.addWidget(self.status_card)
        stats_layout.addWidget(self.modified_card)
        layout.addLayout(stats_layout)

        self.repo_status_label = QLabel("Select a repository to view details.")
        self.repo_status_label.setWordWrap(True)
        layout.addWidget(self.repo_status_label)

        quick_actions = QHBoxLayout()
        self.pull_button = QPushButton("Pull Latest")
        self.pull_button.clicked.connect(self._on_pull_latest)
        self.push_button = QPushButton("Push Changes")
        self.push_button.clicked.connect(self._on_push_changes)
        self.new_branch_button = QPushButton("New Branch")
        self.new_branch_button.clicked.connect(self._on_new_branch)
        quick_actions.addWidget(self.pull_button)
        quick_actions.addWidget(self.push_button)
        quick_actions.addWidget(self.new_branch_button)
        layout.addLayout(quick_actions)

        layout.addStretch(1)
        return widget

    def _create_stat_card(self, title: str, value: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setProperty("card", True)
        card_layout = QVBoxLayout(card)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #9aa0aa;")
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        return card, value_label

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
        self.add_repo_action = QAction("Add Existing Repo", self)
        self.add_repo_action.triggered.connect(self._on_add_repo)
        file_menu.addAction(self.add_repo_action)
        toolbar.addAction(self.add_repo_action)

        clone_repo_action = QAction("Clone Repo", self)
        clone_repo_action.triggered.connect(self._on_clone_repo)
        file_menu.addAction(clone_repo_action)
        toolbar.addAction(clone_repo_action)
        self.clone_repo_action = QAction("Clone Repo", self)
        self.clone_repo_action.triggered.connect(self._on_clone_repo)
        file_menu.addAction(self.clone_repo_action)
        toolbar.addAction(self.clone_repo_action)

        self.remove_repo_action = QAction("Remove Selected Repo", self)
        self.remove_repo_action.triggered.connect(self._on_remove_repo)
        file_menu.addAction(self.remove_repo_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = self.menuBar().addMenu("Tools")

        rescan_action = QAction("Rescan Base Directory", self)
        rescan_action.triggered.connect(self._on_rescan_repositories)
        tools_menu.addAction(rescan_action)

        open_base_action = QAction("Open Base Directory", self)
        open_base_action.triggered.connect(self._open_base_directory)
        tools_menu.addAction(open_base_action)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.log_dock.toggleViewAction())
        view_menu.addAction(self.activity_dock.toggleViewAction())
        view_menu.addAction(toolbar.toggleViewAction())

        help_menu = self.menuBar().addMenu("Help")
        about_action = QAction("About GitBoss", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _on_repo_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            self.current_repo = None
            self.repo_status_label.setText("No repository selected.")
            self.repo_title_label.setText("Select a repository to begin.")
            self._update_stat_cards(branches="—", status="—", modified="—")
            self._set_repo_actions_enabled(False)
            return
        self.current_repo = Path(current.data(Qt.UserRole))
        self.status_bar.showMessage(f"Selected repository: {self.current_repo}")
        self.repo_title_label.setText(self.current_repo.name)
        self._set_repo_actions_enabled(True)
        self._refresh_current_repo()

    def _refresh_current_repo(self) -> None:
        if self.current_repo is None:
            return
        try:
            manager = GitManager(self.current_repo)
            dirty = manager.is_dirty()
            branches = ", ".join(manager.list_branches())
            branch_list = manager.list_branches()
            branches = ", ".join(branch_list)
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
        self._update_stat_cards(
            branches=str(len(branch_list)),
            status="Dirty" if dirty else "Clean",
            modified=str(len(status_lines)),
        )
        self._log_activity(f"Loaded repository {self.current_repo.name}")

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
            self._log_activity(f"Added repository {path.name}")

    def _on_clone_repo(self) -> None:
        QMessageBox.information(self, "Clone Repository", "Clone functionality will be available soon.")
        self._log_activity("Viewed clone repository flow")

    def _on_remove_repo(self) -> None:
        current_item = self.repo_list_widget.currentItem()
        if current_item is None:
            QMessageBox.information(self, "Remove Repository", "Select a repository to remove.")
            return
        repo_path = Path(current_item.data(Qt.UserRole))
        if repo_path in self.repos:
            self.repos.remove(repo_path)
            self.repo_list_widget.populate(self.repos)
            self._persist_repositories()
            self._log_activity(f"Removed repository {repo_path.name}")

    def _on_rescan_repositories(self) -> None:
        if not self.config.base_directory:
            QMessageBox.information(self, "Rescan Repositories", "Set a base directory first.")
            return
        scanned = scan_for_repositories(Path(self.config.base_directory))
        merged = list(dict.fromkeys([*self.repos, *scanned]))
        self.repos = merged
        self.repo_list_widget.populate(self.repos)
        self._persist_repositories()
        self._log_activity("Rescanned repositories")

    def _open_base_directory(self) -> None:
        if not self.config.base_directory:
            QMessageBox.information(self, "Open Base Directory", "Set a base directory first.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.config.base_directory))
        self._log_activity("Opened base directory")

    def _open_in_file_manager(self) -> None:
        if self.current_repo is None:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.current_repo)))
        self._log_activity(f"Opened {self.current_repo.name} in file manager")

    def _copy_repo_path(self) -> None:
        if self.current_repo is None:
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(str(self.current_repo))
        self.status_bar.showMessage("Repository path copied to clipboard.")
        self._log_activity("Copied repository path")

    def _on_pull_latest(self) -> None:
        QMessageBox.information(self, "Pull Latest", "Pull functionality will be available soon.")
        self._log_activity("Viewed pull latest action")

    def _on_push_changes(self) -> None:
        QMessageBox.information(self, "Push Changes", "Push functionality will be available soon.")
        self._log_activity("Viewed push changes action")

    def _on_new_branch(self) -> None:
        QMessageBox.information(self, "New Branch", "Branch creation will be available soon.")
        self._log_activity("Viewed new branch action")

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About GitBoss",
            "GitBoss helps you manage repositories with a sleek dashboard, quick actions, and insights.",
        )

    def _filter_repositories(self, text: str) -> None:
        query = text.lower().strip()
        for index in range(self.repo_list_widget.count()):
            item = self.repo_list_widget.item(index)
            item.setHidden(query not in item.text().lower())

    def _update_stat_cards(self, branches: str, status: str, modified: str) -> None:
        self.branch_value_label.setText(branches)
        self.status_value_label.setText(status)
        self.modified_value_label.setText(modified)

    def _set_repo_actions_enabled(self, enabled: bool) -> None:
        self.open_button.setEnabled(enabled)
        self.copy_button.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.pull_button.setEnabled(enabled)
        self.push_button.setEnabled(enabled)
        self.new_branch_button.setEnabled(enabled)

    def _log_activity(self, message: str) -> None:
        self.activity_list.addItem(message)
        self.activity_list.scrollToBottom()

    def _persist_repositories(self) -> None:
        self.config.preferences["repositories"] = [str(repo) for repo in self.repos]
        save_config(self.config)


__all__ = ["MainWindow"]