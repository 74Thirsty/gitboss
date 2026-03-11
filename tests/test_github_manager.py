from types import SimpleNamespace

import pytest

from gitboss.core.github_manager import (
    GitHubManager,
    WorkflowArtifactSummary,
    WorkflowRunSummary,
    WorkflowSummary,
)


class DummyRun:
    def __init__(self, run_id: int):
        self.id = run_id
        self.name = "CI"
        self.status = "completed"
        self.conclusion = "success"
        self.html_url = f"https://example.com/runs/{run_id}"
        self.event = "push"
        self.head_branch = "main"
        self.head_sha = "abc123"
        self._rerun_called = False
        self._cancel_called = False

    def rerun(self):
        self._rerun_called = True
        return True

    def cancel(self):
        self._cancel_called = True
        return True

    def logs_url(self):
        return f"https://example.com/runs/{self.id}/logs.zip"

    def get_artifacts(self):
        return [
            SimpleNamespace(
                id=11,
                name="coverage",
                size_in_bytes=2048,
                archive_download_url="https://example.com/artifacts/11.zip",
                expired=False,
            )
        ]


class DummyWorkflow:
    def __init__(self):
        self.dispatches = []

    def get_runs(self, **kwargs):
        self.last_get_runs_kwargs = kwargs
        return [DummyRun(99)]

    def create_dispatch(self, ref, inputs):
        self.dispatches.append((ref, inputs))
        return True


class DummyRepo:
    def __init__(self):
        self.workflow = DummyWorkflow()

    def get_workflows(self):
        return [SimpleNamespace(id=1, name="CI", path=".github/workflows/ci.yml", state="active")]

    def get_workflow(self, workflow_id):
        assert workflow_id == 1
        return self.workflow

    def get_workflow_run(self, run_id):
        assert run_id == 99
        return DummyRun(run_id)


class DummyClient:
    def __init__(self):
        self.repo = DummyRepo()

    def get_repo(self, full_name):
        assert full_name == "octo/repo"
        return self.repo

    def get_user(self):
        return SimpleNamespace(get_repos=lambda: [SimpleNamespace(full_name="octo/repo")])


def test_methods_require_authentication():
    manager = GitHubManager()

    with pytest.raises(RuntimeError):
        manager.list_repositories()


def test_list_repositories_and_workflows():
    manager = GitHubManager(token="x")
    manager.client = DummyClient()

    repos = manager.list_repositories()
    workflows = manager.list_workflows("octo/repo")

    assert repos == ["octo/repo"]
    assert workflows == [WorkflowSummary(id=1, name="CI", path=".github/workflows/ci.yml", state="active")]


def test_workflow_run_operations():
    manager = GitHubManager(token="x")
    manager.client = DummyClient()

    runs = manager.list_workflow_runs("octo/repo", 1, branch="main", event="push", status="completed")
    assert runs == [
        WorkflowRunSummary(
            id=99,
            name="CI",
            status="completed",
            conclusion="success",
            html_url="https://example.com/runs/99",
            event="push",
            head_branch="main",
            head_sha="abc123",
        )
    ]

    assert manager.dispatch_workflow("octo/repo", 1, ref="main", inputs={"python": "3.12"}) is True
    assert manager.rerun_workflow("octo/repo", 99) is True
    assert manager.cancel_workflow("octo/repo", 99) is True
    assert manager.get_workflow_logs_url("octo/repo", 99) == "https://example.com/runs/99/logs.zip"
    assert manager.list_workflow_artifacts("octo/repo", 99) == [
        WorkflowArtifactSummary(
            id=11,
            name="coverage",
            size_in_bytes=2048,
            archive_download_url="https://example.com/artifacts/11.zip",
            expired=False,
        )
    ]
