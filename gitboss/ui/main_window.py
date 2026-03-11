"""Main application window for GitBoss."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterable, List

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core.git_manager import GitCommitSummary, GitManager
from ..core.github_manager import GitHubManager
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
        self.setFont(QFont("Fira Code", 10))
<<<<<<< ours
=======

    def append_lines(self, lines: Iterable[str]) -> None:
        self.append("\n".join(lines))
>>>>>>> theirs


class MainWindow(QMainWindow):
    """Primary UI for GitBoss."""

    def __init__(self, config: AppConfig, repos: List[Path]) -> None:
        super().__init__()
        self.config = config
        self.repos = repos
        self.current_repo: Path | None = None
        self.current_commits: list[GitCommitSummary] = []
        self.github_manager: GitHubManager | None = None

        self.setWindowTitle("GitBoss")
        self.resize(1400, 900)
        self._apply_theme()

        self.repo_list_widget = RepositoryListWidget()
        self.repo_list_widget.populate(self.repos)
        self.repo_list_widget.currentItemChanged.connect(self._on_repo_selected)

        self.repo_filter = QLineEdit()
        self.repo_filter.setPlaceholderText("Filter repositories...")
        self.repo_filter.textChanged.connect(self._filter_repositories)

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.addTab(self._create_dashboard_tab(), "Dashboard")
        self.tab_widget.addTab(self._create_commits_tab(), "Commits")
        self.tab_widget.addTab(self._create_diffs_tab(), "Diffs")
        self.tab_widget.addTab(self._create_issues_tab(), "Issues")
        self.tab_widget.addTab(self._create_pr_tab(), "PRs")
        self.tab_widget.addTab(self._create_settings_tab(), "Settings")

        self._build_main_layout()
        self._build_docks()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self._create_menus()
        self._set_repo_actions_enabled(False)
        if self.repos:
            self.repo_list_widget.setCurrentRow(0)

    def _build_main_layout(self) -> None:
        central_widget = QWidget()
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

    def _build_docks(self) -> None:
        self.log_console = LogConsole()
        self.log_dock = QDockWidget("Command Log", self)
        self.log_dock.setWidget(self.log_console)
        self.log_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)

        self.activity_list = QListWidget()
        self.activity_dock = QDockWidget("Activity Feed", self)
        self.activity_dock.setWidget(self.activity_list)
        self.activity_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.activity_dock)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background-color: #0f1115; color: #e6e6e6; }
            QLabel { color: #e6e6e6; }
<<<<<<< ours
            QLineEdit { background-color: #1a1e24; border: 1px solid #2a2f3a; border-radius: 6px; padding: 6px 8px; color: #e6e6e6; }
            QListWidget, QTextEdit { background-color: #151820; border: 1px solid #2a2f3a; border-radius: 8px; padding: 6px; color: #e6e6e6; }
            QPushButton { background-color: #2d6cdf; color: white; border: none; border-radius: 6px; padding: 6px 12px; }
            QPushButton:hover { background-color: #3b7bff; }
            QPushButton:disabled { background-color: #3b3f4a; color: #9aa0aa; }
            QTabWidget::pane { border: 1px solid #2a2f3a; border-radius: 8px; }
            QTabBar::tab { background-color: #151820; padding: 8px 14px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background-color: #232935; }
            QFrame[card="true"] { background-color: #151820; border: 1px solid #2a2f3a; border-radius: 10px; }
=======
            QLineEdit, QSpinBox {
                background-color: #1a1e24;
                border: 1px solid #2a2f3a;
                border-radius: 6px;
                padding: 6px 8px;
                color: #e6e6e6;
            }
            QListWidget, QTextEdit, QPlainTextEdit {
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
            QPushButton:hover { background-color: #3b7bff; }
            QPushButton:pressed { background-color: #1f4ea8; }
            QPushButton:disabled { background-color: #3b3f4a; color: #9aa0aa; }
            QTabWidget::pane { border: 1px solid #2a2f3a; border-radius: 8px; }
            QTabBar::tab {
                background-color: #151820;
                color: #b8bec9;
                padding: 9px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #2a2f3a;
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:hover { background-color: #1d2330; color: #f0f4ff; }
            QTabBar::tab:selected {
                background-color: #232935;
                color: #ffffff;
                font-weight: 700;
                border-top: 2px solid #4c8dff;
            }
            QFrame[card="true"] {
                background-color: #151820;
                border: 1px solid #2a2f3a;
                border-radius: 10px;
            }
>>>>>>> theirs
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

        self.custom_git_command = QLineEdit()
        self.custom_git_command.setPlaceholderText("Run git command (example: rebase -i HEAD~5)")
        self.run_git_command_button = QPushButton("Run Git Command")
        self.run_git_command_button.clicked.connect(self._on_run_git_command)

        command_layout = QHBoxLayout()
        command_layout.addWidget(self.custom_git_command, stretch=1)
        command_layout.addWidget(self.run_git_command_button)
        layout.addLayout(command_layout)

        layout.addStretch(1)
        return widget

    def _create_commits_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        top_bar = QHBoxLayout()
        self.commit_limit = QSpinBox()
        self.commit_limit.setRange(10, 2000)
        self.commit_limit.setValue(200)
        self.commit_limit.setSingleStep(10)
        self.commit_refresh_button = QPushButton("Load Commit Graph")
        self.commit_refresh_button.clicked.connect(self._refresh_commits)
        top_bar.addWidget(QLabel("Commit limit:"))
        top_bar.addWidget(self.commit_limit)
        top_bar.addWidget(self.commit_refresh_button)
        top_bar.addStretch(1)
        layout.addLayout(top_bar)

        panels = QHBoxLayout()
        self.commit_list = QListWidget()
        self.commit_list.currentRowChanged.connect(self._on_commit_selected)
        self.commit_detail = QPlainTextEdit()
        self.commit_detail.setReadOnly(True)
        panels.addWidget(self.commit_list, stretch=2)
        panels.addWidget(self.commit_detail, stretch=3)
        layout.addLayout(panels)
        return widget

    def _create_diffs_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form = QFormLayout()
        self.diff_base_ref = QLineEdit()
        self.diff_base_ref.setPlaceholderText("Base ref (default HEAD~1)")
        self.diff_target_ref = QLineEdit()
        self.diff_target_ref.setPlaceholderText("Target ref (default HEAD)")
        form.addRow("Base", self.diff_base_ref)
        form.addRow("Target", self.diff_target_ref)
        layout.addLayout(form)

        self.diff_refresh_button = QPushButton("Compute Diff")
        self.diff_refresh_button.clicked.connect(self._refresh_diffs)
        layout.addWidget(self.diff_refresh_button)

        self.diff_summary = QPlainTextEdit()
        self.diff_summary.setReadOnly(True)
        self.diff_patch = QPlainTextEdit()
        self.diff_patch.setReadOnly(True)
        layout.addWidget(QLabel("Diffstat"))
        layout.addWidget(self.diff_summary, stretch=1)
        layout.addWidget(QLabel("Patch"))
        layout.addWidget(self.diff_patch, stretch=3)
        return widget

    def _create_issues_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.issues_repo_input = QLineEdit()
        self.issues_repo_input.setPlaceholderText("owner/repo")
        self.issues_refresh_button = QPushButton("Load Open Issues")
        self.issues_refresh_button.clicked.connect(self._refresh_issues)
        self.issues_output = QPlainTextEdit()
        self.issues_output.setReadOnly(True)
        layout.addWidget(QLabel("GitHub repository"))
        layout.addWidget(self.issues_repo_input)
        layout.addWidget(self.issues_refresh_button)
        layout.addWidget(self.issues_output, stretch=1)
        return widget

    def _create_pr_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.pr_repo_input = QLineEdit()
        self.pr_repo_input.setPlaceholderText("owner/repo")
        self.pr_refresh_button = QPushButton("Load Open PRs")
        self.pr_refresh_button.clicked.connect(self._refresh_prs)
        self.pr_output = QPlainTextEdit()
        self.pr_output.setReadOnly(True)
        layout.addWidget(QLabel("GitHub repository"))
        layout.addWidget(self.pr_repo_input)
        layout.addWidget(self.pr_refresh_button)
        layout.addWidget(self.pr_output, stretch=1)
        return widget

    def _create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.settings_base_directory = QLineEdit(self.config.base_directory)
        self.settings_theme = QLineEdit(self.config.default_theme)
        self.settings_github_token = QLineEdit(self.config.preferences.get("github_token", ""))
        self.settings_github_token.setEchoMode(QLineEdit.Password)
        form.addRow("Base directory", self.settings_base_directory)
        form.addRow("Theme", self.settings_theme)
        form.addRow("GitHub token", self.settings_github_token)
        layout.addLayout(form)

        self.settings_save_button = QPushButton("Save Settings")
        self.settings_save_button.clicked.connect(self._save_settings)
        layout.addWidget(self.settings_save_button)
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

    def _create_menus(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        file_menu = self.menuBar().addMenu("File")

        self.add_repo_action = QAction("Add Existing Repo", self)
        self.add_repo_action.triggered.connect(self._on_add_repo)
        file_menu.addAction(self.add_repo_action)
        toolbar.addAction(self.add_repo_action)

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

        run_git_action = QAction("Run Git Command...", self)
        run_git_action.triggered.connect(self._prompt_run_git_command)
        tools_menu.addAction(run_git_action)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.log_dock.toggleViewAction())
        view_menu.addAction(self.activity_dock.toggleViewAction())
        view_menu.addAction(toolbar.toggleViewAction())

        help_menu = self.menuBar().addMenu("Help")
        about_action = QAction("About GitBoss", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _on_tab_changed(self, index: int) -> None:
        tab_name = self.tab_widget.tabText(index)
        self.status_bar.showMessage(f"Active tab: {tab_name}")
        self._log_activity(f"Switched to {tab_name} tab")

    def _on_repo_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        del previous
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
        self._refresh_commits()

    def _refresh_current_repo(self) -> None:
        if self.current_repo is None:
            return

        try:
            manager = GitManager(self.current_repo)
            dirty = manager.is_dirty()
            branch_list = manager.list_branches()
<<<<<<< ours
            branches = ", ".join(branch_list)
=======
>>>>>>> theirs
            status_lines = list(manager.list_status())
        except ValueError as exc:
            QMessageBox.critical(self, "Repository Error", str(exc))
            LOGGER.exception("Failed to load repository")
            return

        details = [
            f"Path: {self.current_repo}",
            f"Branches: {', '.join(branch_list) or 'None'}",
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

    def _refresh_commits(self) -> None:
        if self.current_repo is None:
            return
        try:
            manager = GitManager(self.current_repo)
            self.current_commits = manager.list_commits(limit=self.commit_limit.value())
        except ValueError as exc:
            QMessageBox.critical(self, "Commit Error", str(exc))
            return
        self.commit_list.clear()
        for commit in self.current_commits:
            self.commit_list.addItem(
                f"{commit.short_sha} {commit.subject} | {commit.author_name} | {commit.authored_datetime}"
            )
        if self.current_commits:
            self.commit_list.setCurrentRow(0)
        self._log_activity(f"Loaded {len(self.current_commits)} commits")

    def _on_commit_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.current_commits) or self.current_repo is None:
            return
        commit = self.current_commits[row]
        manager = GitManager(self.current_repo)
        detail = manager.get_commit_details(commit.sha)
        detail_lines = [
            f"Commit: {detail.sha}",
            f"Author: {detail.author_name} <{detail.author_email}>",
            f"Date: {detail.authored_datetime}",
            f"Parents: {', '.join(detail.parents) if detail.parents else 'root'}",
            "",
            "Message:",
            detail.message.strip(),
            "",
            "File Change Summary:",
        ]
        for file_change in detail.file_summaries:
            detail_lines.append(
                f"- {file_change.path} | +{file_change.insertions} -{file_change.deletions} ({file_change.change_type})"
            )
        self.commit_detail.setPlainText("\n".join(detail_lines))

    def _refresh_diffs(self) -> None:
        if self.current_repo is None:
            return
        base_ref = self.diff_base_ref.text().strip() or "HEAD~1"
        target_ref = self.diff_target_ref.text().strip() or "HEAD"
        manager = GitManager(self.current_repo)
        try:
            diff_stat = manager.diff_stat(base_ref, target_ref)
            diff_patch = manager.diff_patch(base_ref, target_ref)
        except ValueError as exc:
            QMessageBox.critical(self, "Diff Error", str(exc))
            return
        self.diff_summary.setPlainText(diff_stat)
        self.diff_patch.setPlainText(diff_patch)
        self._log_activity(f"Computed diff {base_ref}..{target_ref}")

    def _refresh_issues(self) -> None:
        repo = self.issues_repo_input.text().strip()
        if not repo:
            self.issues_output.setPlainText("Set repository as owner/repo.")
            return
        manager = self._github_manager_or_none()
        if manager is None:
            self.issues_output.setPlainText("GitHub token required. Set it in Settings.")
            return
        try:
            issues = manager.list_open_issues(repo)
        except Exception as exc:  # noqa: BLE001
            self.issues_output.setPlainText(str(exc))
            return
        if not issues:
            self.issues_output.setPlainText("No open issues.")
            return
        lines = [f"#{issue.number} {issue.title} [{issue.state}] - {issue.html_url}" for issue in issues]
        self.issues_output.setPlainText("\n".join(lines))

    def _refresh_prs(self) -> None:
        repo = self.pr_repo_input.text().strip()
        if not repo:
            self.pr_output.setPlainText("Set repository as owner/repo.")
            return
        manager = self._github_manager_or_none()
        if manager is None:
            self.pr_output.setPlainText("GitHub token required. Set it in Settings.")
            return
        try:
            pull_requests = manager.list_open_pull_requests(repo)
        except Exception as exc:  # noqa: BLE001
            self.pr_output.setPlainText(str(exc))
            return
        if not pull_requests:
            self.pr_output.setPlainText("No open pull requests.")
            return
        lines = [
            f"#{pr.number} {pr.title} | {pr.user_login} | {pr.head_ref} -> {pr.base_ref} | {pr.html_url}"
            for pr in pull_requests
        ]
        self.pr_output.setPlainText("\n".join(lines))

    def _save_settings(self) -> None:
        self.config.base_directory = self.settings_base_directory.text().strip()
        self.config.default_theme = self.settings_theme.text().strip() or "dark"
        token = self.settings_github_token.text().strip()
        if token:
            self.config.preferences["github_token"] = token
        elif "github_token" in self.config.preferences:
            del self.config.preferences["github_token"]
        save_config(self.config)
        self.github_manager = None
        self.status_bar.showMessage("Settings saved")
        self._log_activity("Saved settings")

    def _github_manager_or_none(self) -> GitHubManager | None:
        token = self.config.preferences.get("github_token", "")
        if not token:
            return None
        if self.github_manager is None:
            manager = GitHubManager(token)
            manager.authenticate()
            self.github_manager = manager
        return self.github_manager

    def _on_add_repo(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Repository Directory", self.config.base_directory)
        if not directory:
            return

        path = Path(directory)
        if path not in self.repos:
            self.repos.append(path)
            self.repo_list_widget.populate(self.repos)
            self.repo_list_widget.setCurrentRow(self.repos.index(path))
            self._persist_repositories()
            self._log_activity(f"Added repository {path.name}")

    def _on_clone_repo(self) -> None:
<<<<<<< ours
        url, ok = QInputDialog.getText(self, "Clone Repository", "Repository URL:")
        if not ok or not url.strip():
            return

        target_dir = QFileDialog.getExistingDirectory(
            self,
            "Clone Into Directory",
            self.config.base_directory or str(Path.home()),
        )
        if not target_dir:
            return

        destination_name, ok = QInputDialog.getText(
            self,
            "Clone Repository",
            "Destination folder name (optional):",
        )
        if not ok:
            return

        destination_path = Path(target_dir)
        if destination_name.strip():
            destination_path = destination_path / destination_name.strip()

        try:
            GitManager.clone(url.strip(), destination_path)
        except Exception as exc:
            LOGGER.exception("Clone failed")
            QMessageBox.critical(self, "Clone Failed", str(exc))
            self._log_activity(f"Clone failed: {exc}")
            return

        if destination_path not in self.repos:
            self.repos.append(destination_path)
            self.repo_list_widget.populate(self.repos)
            self.repo_list_widget.setCurrentRow(self.repos.index(destination_path))
            self._persist_repositories()

        self._log_activity(f"Cloned repository into {destination_path}")
        self.status_bar.showMessage(f"Cloned repository into {destination_path}", 5000)
=======
        QMessageBox.information(self, "Clone Repository", "Clone workflow is not yet implemented.")
        self._log_activity("Viewed clone repository flow")
>>>>>>> theirs

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
        self.repos = list(dict.fromkeys([*self.repos, *scanned]))
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
        QApplication.clipboard().setText(str(self.current_repo))
        self.status_bar.showMessage("Repository path copied to clipboard.")
        self._log_activity("Copied repository path")

    def _on_pull_latest(self) -> None:
<<<<<<< ours
        branch, ok = QInputDialog.getText(self, "Pull Latest", "Branch to pull (leave blank for current):")
        if not ok:
            return
        branch_name = branch.strip() or None

        def operation(manager: GitManager) -> str:
            return manager.pull(branch=branch_name)

        branch_text = branch_name or "current"
        self._run_repo_operation(operation, f"Pulled latest from origin/{branch_text}")

    def _on_push_changes(self) -> None:
        branch, ok = QInputDialog.getText(self, "Push Changes", "Branch to push (leave blank for current):")
        if not ok:
            return
        branch_name = branch.strip() or None

        def operation(manager: GitManager) -> str:
            return manager.push(branch=branch_name)

        branch_text = branch_name or "current"
        self._run_repo_operation(operation, f"Pushed changes to origin/{branch_text}")

    def _on_new_branch(self) -> None:
        branch_name, ok = QInputDialog.getText(self, "New Branch", "New branch name:")
        if not ok:
            return
        clean_name = branch_name.strip()
        if not clean_name:
            QMessageBox.information(self, "New Branch", "Branch name cannot be empty.")
            return

        def operation(manager: GitManager) -> str:
            return manager.create_branch(clean_name, checkout=True)

        self._run_repo_operation(operation, f"Created and checked out branch {clean_name}")

    def _on_run_git_command(self) -> None:
        command = self.custom_git_command.text().strip()
        if not command:
            QMessageBox.information(self, "Run Git Command", "Enter a git command first.")
            return

        def operation(manager: GitManager) -> str:
            return manager.run_git_command(command)

        self._run_repo_operation(operation, f"Ran git {command}")

    def _prompt_run_git_command(self) -> None:
        command, ok = QInputDialog.getText(self, "Run Git Command", "Git command (omit leading 'git'):")
        if not ok or not command.strip():
            return
        self.custom_git_command.setText(command.strip())
        self._on_run_git_command()

    def _run_repo_operation(self, operation: Callable[[GitManager], str], success_message: str) -> None:
        if self.current_repo is None:
            QMessageBox.information(self, "Git Operation", "Select a repository first.")
            return

        try:
            manager = GitManager(self.current_repo)
            output = operation(manager)
        except Exception as exc:
            LOGGER.exception("Git operation failed")
            QMessageBox.critical(self, "Git Operation Failed", str(exc))
            self._log_activity(f"Git operation failed: {exc}")
            return

        if output:
            self.log_console.append(f"$ {success_message}\n{output}")
        self.status_bar.showMessage(success_message, 5000)
        self._log_activity(success_message)
        self._refresh_current_repo()
=======
        if self.current_repo is None:
            return
        try:
            manager = GitManager(self.current_repo)
            result = manager.pull()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Pull Error", str(exc))
            return
        self.log_console.append(result)
        self._refresh_current_repo()

    def _on_push_changes(self) -> None:
        if self.current_repo is None:
            return
        try:
            manager = GitManager(self.current_repo)
            result = manager.push()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Push Error", str(exc))
            return
        self.log_console.append(result)
        self._refresh_current_repo()

    def _on_new_branch(self) -> None:
        QMessageBox.information(self, "New Branch", "Branch creation workflow is not yet implemented.")
>>>>>>> theirs

    def _show_about_dialog(self) -> None:
        QMessageBox.information(self, "About GitBoss", "GitBoss is a Git workspace for local + GitHub operations.")

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
<<<<<<< ours
        self.run_git_command_button.setEnabled(enabled)
        self.custom_git_command.setEnabled(enabled)
=======
        self.commit_refresh_button.setEnabled(enabled)
        self.diff_refresh_button.setEnabled(enabled)
>>>>>>> theirs

    def _log_activity(self, message: str) -> None:
        self.activity_list.addItem(message)
        self.activity_list.scrollToBottom()

    def _persist_repositories(self) -> None:
        self.config.preferences["repositories"] = [str(repo) for repo in self.repos]
        save_config(self.config)


__all__ = ["MainWindow"]
