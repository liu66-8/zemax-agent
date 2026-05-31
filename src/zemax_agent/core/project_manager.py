from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from zemax_agent.core.database import SQLiteStore, ProjectRecord
from zemax_agent.core.project import ProjectMeta, DesignPhase, ProjectWorkspace

logger = logging.getLogger(__name__)


class ProjectManager:
    def __init__(self, store: SQLiteStore, workspace_base: str | Path = "./workspace"):
        self._store = store
        self._workspace_base = Path(workspace_base).resolve()
        self._workspace_base.mkdir(parents=True, exist_ok=True)
        self._open_project: Optional[ProjectMeta] = None
        self._open_workspace: Optional[ProjectWorkspace] = None

    @property
    def current_project(self) -> Optional[ProjectMeta]:
        return self._open_project

    @property
    def current_workspace(self) -> Optional[ProjectWorkspace]:
        return self._open_workspace

    def create(self, name: str, description: str = "", system_type: str = "",
               tags: Optional[list[str]] = None, zmx_source: Optional[str | Path] = None) -> ProjectMeta:
        project_id = str(uuid.uuid4())
        workspace_path = self._workspace_base / project_id

        workspace = ProjectWorkspace(workspace_path)
        workspace.initialize()

        meta = ProjectMeta(
            id=project_id,
            name=name,
            description=description,
            system_type=system_type,
            design_phase=DesignPhase.REQUIREMENTS,
            tags=tags or [],
            workspace_path=str(workspace_path),
        )

        if zmx_source:
            zmx_src = Path(zmx_source)
            if zmx_src.exists():
                dest = workspace.designs_dir / zmx_src.name
                import shutil
                shutil.copy2(zmx_src, dest)
                meta.zmx_path = str(dest)

        workspace.save_manifest(meta)
        self._store.create_project(self._meta_to_record(meta))
        logger.info("Project created: %s (%s)", name, project_id[:8])
        return meta

    def open(self, project_id: str) -> ProjectMeta:
        record = self._store.get_project(project_id)
        if record is None:
            raise FileNotFoundError(f"Project not found: {project_id}")

        meta = ProjectMeta(
            id=record.id, name=record.name, description=record.description,
            system_type=record.system_type, design_phase=DesignPhase(record.design_phase),
            tags=record.tags, workspace_path=record.workspace_path,
            zmx_path=record.zmx_path, created_at=record.created_at,
            updated_at=record.updated_at, archived_at=record.archived_at,
            metadata=record.metadata,
        )

        self._open_project = meta
        self._open_workspace = ProjectWorkspace(meta.workspace_path)
        logger.info("Project opened: %s (%s)", meta.name, project_id[:8])
        return meta

    def close(self) -> None:
        if self._open_project:
            self._save_state()
            logger.info("Project closed: %s", self._open_project.name[:8])
        self._open_project = None
        self._open_workspace = None

    def delete(self, project_id: str) -> bool:
        record = self._store.get_project(project_id)
        if record is None:
            return False

        if self._open_project and self._open_project.id == project_id:
            self.close()

        workspace_path = Path(record.workspace_path)
        if workspace_path.exists():
            import shutil
            shutil.rmtree(workspace_path, ignore_errors=True)

        success = self._store.delete_project(project_id)
        logger.info("Project deleted: %s", project_id[:8])
        return success

    def archive(self, project_id: Optional[str] = None) -> Optional[ProjectMeta]:
        pid = project_id or (self._open_project.id if self._open_project else None)
        if pid is None:
            return None

        record = self._store.archive_project(pid)
        if record is None:
            return None
        return self._record_to_meta(record)

    def unarchive(self, project_id: str) -> Optional[ProjectMeta]:
        record = self._store.unarchive_project(project_id)
        if record is None:
            return None
        return self._record_to_meta(record)

    def list_active(self) -> list[ProjectMeta]:
        records = self._store.list_projects(archived=False)
        return [self._record_to_meta(r) for r in records]

    def list_archived(self) -> list[ProjectMeta]:
        records = self._store.list_projects(archived=True)
        return [self._record_to_meta(r) for r in records]

    def list_by_tag(self, tag: str) -> list[ProjectMeta]:
        records = self._store.list_projects(archived=False, tag=tag)
        return [self._record_to_meta(r) for r in records]

    def update_meta(self, **kwargs: Any) -> Optional[ProjectMeta]:
        if self._open_project is None:
            return None

        valid_fields = {"name", "description", "system_type", "design_phase", "tags", "zmx_path", "metadata"}
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}

        if "design_phase" in updates and not isinstance(updates["design_phase"], str):
            updates["design_phase"] = updates["design_phase"].value

        record = self._store.update_project(self._open_project.id, **updates)
        if record is None:
            return None

        meta = self._record_to_meta(record)
        self._open_project = meta
        if self._open_workspace:
            self._open_workspace.save_manifest(meta)
        return meta

    def update_phase(self, phase: DesignPhase) -> Optional[ProjectMeta]:
        return self.update_meta(design_phase=phase)

    def export_project(self, output_path: str | Path) -> Path:
        if self._open_workspace is None:
            raise RuntimeError("No project open")
        return self._open_workspace.export_to_zip(output_path)

    def import_project(self, zip_path: str | Path) -> ProjectMeta:
        zip_src = Path(zip_path)
        project_id = str(uuid.uuid4())
        target_dir = self._workspace_base / project_id

        workspace = ProjectWorkspace.import_from_zip(zip_src, target_dir)
        meta = workspace.load_manifest(str(target_dir))
        meta.id = project_id
        workspace.save_manifest(meta)

        self._store.create_project(self._meta_to_record(meta))
        logger.info("Project imported: %s", meta.name)
        return meta

    def get_data_relations(self, project_id: Optional[str] = None) -> dict[str, Any]:
        pid = project_id or (self._open_project.id if self._open_project else None)
        if pid is None:
            return {}

        return {
            "project_id": pid,
            "tasks": [t.model_dump() for t in self._store.list_tasks(project_id=pid)],
            "versions": [v.model_dump() for v in self._store.list_versions(pid)],
            "sessions": [s.model_dump() for s in self._store.list_sessions(pid)],
            "operation_logs": [o.model_dump() for o in self._store.list_operation_logs(project_id=pid, limit=50)],
        }

    def _save_state(self) -> None:
        if self._open_project:
            self._open_project.updated_at = datetime.now(timezone.utc).isoformat()
            self._store.update_project(self._open_project.id, updated_at=self._open_project.updated_at)

    def _meta_to_record(self, meta: ProjectMeta) -> ProjectRecord:
        return ProjectRecord(
            id=meta.id, name=meta.name, description=meta.description,
            system_type=meta.system_type, design_phase=meta.design_phase.value,
            tags=meta.tags, workspace_path=meta.workspace_path,
            zmx_path=meta.zmx_path, created_at=meta.created_at,
            updated_at=meta.updated_at, archived_at=meta.archived_at,
            metadata=meta.metadata,
        )

    def _record_to_meta(self, record: ProjectRecord) -> ProjectMeta:
        return ProjectMeta(
            id=record.id, name=record.name, description=record.description,
            system_type=record.system_type,
            design_phase=DesignPhase(record.design_phase),
            tags=record.tags, workspace_path=record.workspace_path,
            zmx_path=record.zmx_path, created_at=record.created_at,
            updated_at=record.updated_at, archived_at=record.archived_at,
            metadata=record.metadata,
        )
