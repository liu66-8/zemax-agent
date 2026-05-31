import uuid
from pathlib import Path

import pytest
from zemax_agent.core.database import (
    SQLiteStore,
    ProjectRecord,
    TaskRecord,
    VersionRecord,
    SessionRecord,
    OperationLogRecord,
    PerformanceMetricRecord,
)


@pytest.fixture
def store(tmp_path: Path):
    db_path = tmp_path / "test.db"
    s = SQLiteStore(db_path)
    yield s
    s.close()


@pytest.fixture
def project(store: SQLiteStore):
    p = ProjectRecord(
        id=str(uuid.uuid4()),
        name="Test Project",
        description="A test optical design",
        system_type="Cooke Triplet",
        design_phase="optimization",
        tags=["test", "demo"],
        workspace_path="/tmp/workspace/test",
        created_at=store._now(),
        updated_at=store._now(),
    )
    return store.create_project(p)


class TestSQLiteStore:
    def test_schema_version(self, store: SQLiteStore):
        assert store.get_schema_version() == 1

    def test_migrate_noop(self, store: SQLiteStore):
        assert store.migrate() == 1


class TestProjectCRUD:
    def test_create_and_get(self, store: SQLiteStore, project: ProjectRecord):
        result = store.get_project(project.id)
        assert result is not None
        assert result.name == "Test Project"

    def test_list_projects(self, store: SQLiteStore, project: ProjectRecord):
        projects = store.list_projects()
        assert len(projects) >= 1

    def test_list_archived(self, store: SQLiteStore, project: ProjectRecord):
        store.archive_project(project.id)
        archived = store.list_projects(archived=True)
        assert len(archived) >= 1
        active = store.list_projects(archived=False)
        assert all(p.id != project.id for p in active)

    def test_update_project(self, store: SQLiteStore, project: ProjectRecord):
        updated = store.update_project(project.id, name="Renamed")
        assert updated is not None
        assert updated.name == "Renamed"

    def test_delete_project(self, store: SQLiteStore, project: ProjectRecord):
        assert store.delete_project(project.id) is True
        assert store.get_project(project.id) is None

    def test_archive_unarchive(self, store: SQLiteStore, project: ProjectRecord):
        archived = store.archive_project(project.id)
        assert archived is not None
        assert archived.archived_at is not None

        unarchived = store.unarchive_project(project.id)
        assert unarchived is not None
        assert unarchived.archived_at is None


class TestTaskCRUD:
    def test_create_and_get(self, store: SQLiteStore, project: ProjectRecord):
        task = TaskRecord(
            id=str(uuid.uuid4()),
            project_id=project.id,
            task_type="optimize",
            status="pending",
            params={"merit_function": "rms"},
            created_at=store._now(),
        )
        store.create_task(task)
        result = store.get_task(task.id)
        assert result is not None
        assert result.task_type == "optimize"

    def test_update_task(self, store: SQLiteStore, project: ProjectRecord):
        task = TaskRecord(
            id=str(uuid.uuid4()),
            project_id=project.id,
            task_type="analysis",
            status="pending",
            created_at=store._now(),
        )
        store.create_task(task)
        updated = store.update_task(task.id, status="running", progress=50.0)
        assert updated is not None
        assert updated.status == "running"
        assert updated.progress == 50.0

    def test_list_by_project(self, store: SQLiteStore, project: ProjectRecord):
        t1 = TaskRecord(
            id=str(uuid.uuid4()), project_id=project.id,
            task_type="a", status="completed", created_at=store._now(),
        )
        t2 = TaskRecord(
            id=str(uuid.uuid4()), project_id=project.id,
            task_type="b", status="pending", created_at=store._now(),
        )
        store.create_task(t1)
        store.create_task(t2)
        tasks = store.list_tasks(project_id=project.id)
        assert len(tasks) == 2


class TestVersionCRUD:
    def test_create_and_list(self, store: SQLiteStore, project: ProjectRecord):
        v = VersionRecord(
            id=str(uuid.uuid4()),
            project_id=project.id,
            version_number=1,
            snapshot_path="/tmp/snap1.zmx",
            change_description="Initial structure",
            performance_metrics={"mtf_avg": 0.65, "rms_spot": 5.2},
            created_at=store._now(),
        )
        store.create_version(v)
        versions = store.list_versions(project.id)
        assert len(versions) == 1
        assert versions[0].performance_metrics["mtf_avg"] == 0.65

    def test_delete_version(self, store: SQLiteStore, project: ProjectRecord):
        v = VersionRecord(
            id=str(uuid.uuid4()),
            project_id=project.id,
            version_number=2,
            snapshot_path="/tmp/snap2.zmx",
            created_at=store._now(),
        )
        store.create_version(v)
        assert store.delete_version(v.id) is True
        assert store.get_version(v.id) is None


class TestSessionCRUD:
    def test_create_and_list(self, store: SQLiteStore, project: ProjectRecord):
        s = SessionRecord(
            id=str(uuid.uuid4()),
            project_id=project.id,
            title="Design discussion",
            thread_id=str(uuid.uuid4()),
            messages=[{"role": "user", "content": "hello"}],
            created_at=store._now(),
            updated_at=store._now(),
        )
        store.create_session(s)
        sessions = store.list_sessions(project.id)
        assert len(sessions) == 1

    def test_update_session(self, store: SQLiteStore, project: ProjectRecord):
        s = SessionRecord(
            id=str(uuid.uuid4()),
            project_id=project.id,
            title="Test",
            thread_id=str(uuid.uuid4()),
            created_at=store._now(),
            updated_at=store._now(),
        )
        store.create_session(s)
        updated = store.update_session(s.id, title="Updated Title")
        assert updated is not None
        assert updated.title == "Updated Title"


class TestOperationLogs:
    def test_log_and_list(self, store: SQLiteStore, project: ProjectRecord):
        log = OperationLogRecord(
            project_id=project.id,
            tool_name="lens.set_radius",
            caller="AI",
            params={"surface": 3, "radius": 100.0},
            duration_ms=150.5,
            created_at=store._now(),
        )
        log_id = store.log_operation(log)
        assert log_id > 0

        logs = store.list_operation_logs(project_id=project.id)
        assert len(logs) == 1
        assert logs[0].tool_name == "lens.set_radius"


class TestPreferences:
    def test_set_get(self, store: SQLiteStore):
        store.set_preference("theme", "dark")
        assert store.get_preference("theme") == "dark"

    def test_get_all(self, store: SQLiteStore):
        store.set_preference("a", "1")
        store.set_preference("b", "2")
        prefs = store.get_all_preferences()
        assert prefs["a"] == "1"
        assert prefs["b"] == "2"

    def test_delete(self, store: SQLiteStore):
        store.set_preference("x", "y")
        assert store.delete_preference("x") is True
        assert store.get_preference("x") is None


class TestPerformanceMetrics:
    def test_save_and_list(self, store: SQLiteStore, project: ProjectRecord):
        m = PerformanceMetricRecord(
            id=str(uuid.uuid4()),
            project_id=project.id,
            metric_type="mtf",
            metric_data={"field_0": 0.8, "field_1": 0.7},
            created_at=store._now(),
        )
        store.save_performance_metric(m)
        metrics = store.list_performance_metrics(project.id)
        assert len(metrics) == 1
        assert metrics[0].metric_data["field_0"] == 0.8
