from pathlib import Path
import time

from zemax_agent.core.database import SQLiteStore, ProjectRecord
from zemax_agent.core.project import DesignPhase
from zemax_agent.core.workflow import WorkflowEngine, DesignContext, PHASE_TRANSITIONS
from zemax_agent.core.task_scheduler import TaskScheduler, Task, TaskType, TaskStatusEnum
from zemax_agent.core.health import HealthMonitor, HealthStatus, ComponentType, SystemHealth
from zemax_agent.core.design_templates import TemplateLibrary, DesignTemplate, TemplateParameter, PRESET_TEMPLATES
from zemax_agent.core.version_manager import VersionManager, DesignSnapshot, PerformanceSnapshot


class TestWorkflowEngine:
    def test_transitions(self):
        engine = WorkflowEngine()
        assert DesignPhase.OPTIMIZATION in engine.get_allowed_transitions(DesignPhase.INITIAL_STRUCTURE)
        assert DesignPhase.REPORT not in engine.get_allowed_transitions(DesignPhase.REQUIREMENTS)

    def test_can_transition(self):
        engine = WorkflowEngine()
        assert engine.can_transition(DesignPhase.OPTIMIZATION, DesignPhase.ANALYSIS)
        assert not engine.can_transition(DesignPhase.REQUIREMENTS, DesignPhase.REPORT)

    def test_transition_execute(self):
        engine = WorkflowEngine()
        ok, msg = engine.transition(DesignPhase.REQUIREMENTS, DesignPhase.INITIAL_STRUCTURE)
        assert ok
        assert engine.get_current_phase() == DesignPhase.INITIAL_STRUCTURE

    def test_transition_same_phase(self):
        engine = WorkflowEngine()
        ok, msg = engine.transition(DesignPhase.ANALYSIS, DesignPhase.ANALYSIS)
        assert ok

    def test_transition_rejected(self):
        engine = WorkflowEngine()
        ok, msg = engine.transition(DesignPhase.REPORT, DesignPhase.REQUIREMENTS)
        assert not ok

    def test_build_context(self):
        engine = WorkflowEngine()
        from zemax_agent.core.project import ProjectMeta
        meta = ProjectMeta(name="Test", description="desc", system_type="Cooke", design_phase=DesignPhase.OPTIMIZATION)
        ctx = engine.build_context(meta, version_count=3, session_count=5)
        assert ctx.project_phase == DesignPhase.OPTIMIZATION
        assert ctx.version_count == 3

    def test_phase_transitions_completeness(self):
        for phase in DesignPhase:
            transitions = PHASE_TRANSITIONS.get(phase, [])
            assert isinstance(transitions, list)


class TestTaskScheduler:
    def _setup_project(self, store: SQLiteStore, proj_id: str, ws: Path):
        ws.mkdir(parents=True, exist_ok=True)
        store.create_project(ProjectRecord(
            id=proj_id, name="ts_test", workspace_path=str(ws),
            created_at=store._now(), updated_at=store._now(),
        ))

    def test_submit_and_start(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        self._setup_project(store, "p1", tmp_path / "workspace" / "p1")
        scheduler = TaskScheduler(store)

        task = Task(project_id="p1", task_type=TaskType.ANALYSIS)
        scheduler.submit(task)
        assert scheduler.pending_count == 1

        started = scheduler.start_next()
        assert started is not None
        assert started.status == TaskStatusEnum.RUNNING
        assert scheduler.running_task is not None

    def test_complete_task(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        self._setup_project(store, "p1", tmp_path / "workspace" / "p1")
        scheduler = TaskScheduler(store)

        task = Task(project_id="p1", task_type=TaskType.OPTIMIZATION)
        scheduler.submit(task)
        scheduler.start_next()
        completed = scheduler.complete_current({"mf": 0.01})
        assert completed is not None
        assert completed.status == TaskStatusEnum.COMPLETED
        assert completed.progress == 100.0

    def test_fail_task(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        self._setup_project(store, "p1", tmp_path / "workspace" / "p1")
        scheduler = TaskScheduler(store)

        task = Task(project_id="p1", task_type=TaskType.ANALYSIS)
        scheduler.submit(task)
        scheduler.start_next()
        failed = scheduler.fail_current("ZOS connection error")
        assert failed is not None
        assert failed.status == TaskStatusEnum.FAILED
        assert failed.error == "ZOS connection error"

    def test_cancel_pending(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        self._setup_project(store, "p1", tmp_path / "workspace" / "p1")
        scheduler = TaskScheduler(store)

        task = Task(project_id="p1", task_type=TaskType.LENS_EDIT)
        scheduler.submit(task)
        assert scheduler.cancel(task.id)
        assert scheduler.pending_count == 0

    def test_cancel_all(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        self._setup_project(store, "p1", tmp_path / "workspace" / "p1")
        scheduler = TaskScheduler(store)

        for _ in range(3):
            scheduler.submit(Task(project_id="p1", task_type=TaskType.ANALYSIS))
        assert scheduler.cancel_all_pending() == 3

    def test_history(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        self._setup_project(store, "p1", tmp_path / "workspace" / "p1")
        scheduler = TaskScheduler(store)

        task = Task(project_id="p1", task_type=TaskType.ANALYSIS)
        scheduler.submit(task)
        scheduler.start_next()
        scheduler.complete_current({"data": "ok"})

        history = scheduler.get_history("p1")
        assert len(history) == 1

    def test_progress_update(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        self._setup_project(store, "p1", tmp_path / "workspace" / "p1")
        scheduler = TaskScheduler(store)

        progress_values = []
        scheduler.set_progress_callback(lambda tid, prog, msg: progress_values.append(prog))

        task = Task(project_id="p1", task_type=TaskType.ANALYSIS)
        scheduler.submit(task)
        scheduler.start_next()
        scheduler.update_progress(50.0, "Half done")
        scheduler.update_progress(80.0, "Almost done")

        assert len(progress_values) == 2
        assert progress_values[0] == 50.0


class TestHealthMonitor:
    def test_check_now(self):
        monitor = HealthMonitor()
        monitor.register_check(ComponentType.SQLITE, lambda: (True, "OK"))
        monitor.register_check(ComponentType.ZOS, lambda: (False, "Not connected"))

        health = monitor.check_now()
        assert health.overall == HealthStatus.UNHEALTHY
        assert health.components["sqlite"].status == HealthStatus.HEALTHY
        assert health.components["zos"].status == HealthStatus.UNHEALTHY

    def test_all_healthy(self):
        monitor = HealthMonitor()
        monitor.register_check(ComponentType.SQLITE, lambda: (True, "OK"))
        monitor.register_check(ComponentType.ZOS, lambda: (True, "Connected"))

        health = monitor.check_now()
        assert health.overall == HealthStatus.HEALTHY

    def test_exception_handling(self):
        monitor = HealthMonitor()
        monitor.register_check(ComponentType.QDRANT, lambda: (_ for _ in ()).throw(Exception("crash")))

        health = monitor.check_now()
        assert health.components["qdrant"].status == HealthStatus.UNHEALTHY

    def test_callbacks(self):
        monitor = HealthMonitor()
        called = []
        monitor.on_health_change(lambda h: called.append(h.overall))
        monitor.register_check(ComponentType.SQLITE, lambda: (True, "OK"))

        monitor.check_now()
        monitor.check_now()
        assert len(called) >= 0


class TestTemplateLibrary:
    def test_preset_count(self):
        lib = TemplateLibrary()
        assert len(lib) >= 5

    def test_get_template(self):
        lib = TemplateLibrary()
        tmpl = lib.get("Cooke Triplet")
        assert tmpl is not None
        assert tmpl.category == "prime_lens"

    def test_categories(self):
        lib = TemplateLibrary()
        cats = lib.get_categories()
        assert "prime_lens" in cats

    def test_list_by_category(self):
        lib = TemplateLibrary()
        primes = lib.list_by_category("prime_lens")
        assert len(primes) >= 2

    def test_generate_params(self):
        lib = TemplateLibrary()
        params = lib.generate_params("Cooke Triplet", {"focal_length": 200.0})
        assert params["focal_length"] == 200.0
        assert params["f_number"] == 4.0


class TestVersionManager:
    def test_create_and_list(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        vm = VersionManager(store)

        proj_id = "p1"
        ws = tmp_path / "workspace" / proj_id
        ws.mkdir(parents=True, exist_ok=True)
        (ws / "snapshots").mkdir(exist_ok=True)

        store.create_project(ProjectRecord(
            id=proj_id, name="vtest", workspace_path=str(ws),
            created_at=store._now(), updated_at=store._now(),
        ))

        zmx = tmp_path / "test.zmx"
        zmx.write_text("dummy zmx")

        snap = vm.create_snapshot(proj_id, zmx, "Initial", PerformanceSnapshot(mtf_avg=0.75, rms_spot_radius=5.0))
        assert snap.version_number == 1

        snaps = vm.list_snapshots(proj_id)
        assert len(snaps) == 1

    def test_compare(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        vm = VersionManager(store)

        proj_id = "p1"
        ws = tmp_path / "workspace" / proj_id
        (ws / "snapshots").mkdir(parents=True, exist_ok=True)

        store.create_project(ProjectRecord(
            id=proj_id, name="vtest", workspace_path=str(ws),
            created_at=store._now(), updated_at=store._now(),
        ))

        zmx = tmp_path / "test.zmx"
        zmx.write_text("dummy")

        s1 = vm.create_snapshot(proj_id, zmx, "v1", PerformanceSnapshot(mtf_avg=0.7, merit_function=0.05))
        s2 = vm.create_snapshot(proj_id, zmx, "v2", PerformanceSnapshot(mtf_avg=0.85, merit_function=0.02))

        diff = vm.compare(s1.id, s2.id)
        assert "diffs" in diff
        assert "mtf_avg" in diff["diffs"]

    def test_trend(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        vm = VersionManager(store)

        proj_id = "p1"
        ws = tmp_path / "workspace" / proj_id
        (ws / "snapshots").mkdir(parents=True, exist_ok=True)

        store.create_project(ProjectRecord(
            id=proj_id, name="vtest", workspace_path=str(ws),
            created_at=store._now(), updated_at=store._now(),
        ))

        zmx = tmp_path / "test.zmx"
        zmx.write_text("dummy")

        vm.create_snapshot(proj_id, zmx, "v1")
        vm.create_snapshot(proj_id, zmx, "v2")
        vm.create_snapshot(proj_id, zmx, "v3")

        trend = vm.get_performance_trend(proj_id)
        assert len(trend) == 3
        assert trend[0]["version_number"] == 1
        assert trend[2]["version_number"] == 3
