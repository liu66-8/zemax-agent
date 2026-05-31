from pathlib import Path

from zemax_agent.core.database import SQLiteStore
from zemax_agent.core.project import ProjectMeta, DesignPhase, ProjectWorkspace
from zemax_agent.core.project_manager import ProjectManager


class TestProjectWorkspace:
    def test_initialize(self, tmp_path: Path):
        ws = ProjectWorkspace(tmp_path / "proj")
        ws.initialize()
        assert ws.designs_dir.exists()
        assert ws.analyses_dir.exists()
        assert ws.reports_dir.exists()
        assert ws.snapshots_dir.exists()
        assert ws.sessions_dir.exists()

    def test_save_load_manifest(self, tmp_path: Path):
        ws = ProjectWorkspace(tmp_path / "proj")
        ws.initialize()
        meta = ProjectMeta(name="Test", description="desc")
        ws.save_manifest(meta)
        loaded = ws.load_manifest(str(ws.root))
        assert loaded.name == "Test"

    def test_export_import_zip(self, tmp_path: Path):
        ws = ProjectWorkspace(tmp_path / "proj")
        ws.initialize()
        meta = ProjectMeta(name="Export Test")
        ws.save_manifest(meta)

        zip_path = tmp_path / "export.zip"
        result = ws.export_to_zip(zip_path)
        assert result.exists()

        imported = ProjectWorkspace.import_from_zip(result, tmp_path / "imported")
        assert (imported.root / "project.json").exists()


class TestProjectManager:
    def test_create_and_open(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        pm = ProjectManager(store, tmp_path / "workspace")

        meta = pm.create("Test Project", description="Test", system_type="Cooke Triplet")
        assert meta.name == "Test Project"
        assert meta.design_phase == DesignPhase.REQUIREMENTS

        opened = pm.open(meta.id)
        assert opened.name == "Test Project"
        assert pm.current_project is not None

        pm.close()

    def test_list_active(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        pm = ProjectManager(store, tmp_path / "workspace")

        pm.create("Project A")
        pm.create("Project B")
        active = pm.list_active()
        assert len(active) == 2

    def test_archive_unarchive(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        pm = ProjectManager(store, tmp_path / "workspace")

        meta = pm.create("Archive Me")
        archived = pm.archive(meta.id)
        assert archived is not None
        assert archived.archived_at is not None

        active = pm.list_active()
        assert not any(p.id == meta.id for p in active)

        unarchived = pm.unarchive(meta.id)
        assert unarchived is not None
        assert unarchived.archived_at is None

    def test_delete(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        pm = ProjectManager(store, tmp_path / "workspace")

        meta = pm.create("Delete Me")
        assert pm.delete(meta.id) is True
        assert pm.list_active() == []

    def test_update_meta(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        pm = ProjectManager(store, tmp_path / "workspace")

        meta = pm.create("Original")
        pm.open(meta.id)
        updated = pm.update_meta(name="Renamed")
        assert updated is not None
        assert updated.name == "Renamed"

    def test_update_phase(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        pm = ProjectManager(store, tmp_path / "workspace")

        meta = pm.create("Phase Test")
        pm.open(meta.id)
        updated = pm.update_phase(DesignPhase.OPTIMIZATION)
        assert updated is not None
        assert updated.design_phase == DesignPhase.OPTIMIZATION

    def test_export_import(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        pm = ProjectManager(store, tmp_path / "workspace")

        meta = pm.create("Export Test")
        pm.open(meta.id)
        zip_path = pm.export_project(tmp_path / "test_export.zip")
        assert zip_path.exists()

        imported = pm.import_project(zip_path)
        assert imported.name == "Export Test"

    def test_data_relations(self, tmp_path: Path):
        store = SQLiteStore(tmp_path / "test.db")
        pm = ProjectManager(store, tmp_path / "workspace")

        meta = pm.create("Relations")
        pm.open(meta.id)
        relations = pm.get_data_relations()
        assert "project_id" in relations
        assert "tasks" in relations
        assert "versions" in relations
        assert "sessions" in relations
        assert "operation_logs" in relations
