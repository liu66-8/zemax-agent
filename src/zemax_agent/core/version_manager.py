from __future__ import annotations

import json
import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from zemax_agent.core.database import SQLiteStore, VersionRecord, PerformanceMetricRecord

logger = logging.getLogger(__name__)


class DesignSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    version_number: int
    snapshot_path: str
    zmx_path: str = ""
    change_description: str = ""
    performance_metrics: dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PerformanceSnapshot(BaseModel):
    mtf_avg: Optional[float] = None
    mtf_tangential: Optional[dict[str, float]] = None
    mtf_sagittal: Optional[dict[str, float]] = None
    rms_spot_radius: Optional[float] = None
    rms_wavefront: Optional[float] = None
    pv_wavefront: Optional[float] = None
    distortion_max: Optional[float] = None
    merit_function: Optional[float] = None


class VersionManager:
    def __init__(self, store: SQLiteStore):
        self._store = store

    def create_snapshot(
        self,
        project_id: str,
        zmx_source_path: str | Path,
        change_description: str = "",
        performance: Optional[PerformanceSnapshot] = None,
        session_id: Optional[str] = None,
    ) -> DesignSnapshot:
        existing = self._store.list_versions(project_id)
        version_number = len(existing) + 1

        snapshot_id = str(uuid.uuid4())

        record = self._store.get_project(project_id)
        if record is None:
            raise FileNotFoundError(f"Project not found: {project_id}")

        workspace = Path(record.workspace_path)
        snapshots_dir = workspace / "snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        zmx_name = Path(zmx_source_path).name or f"v{version_number:03d}.zmx"
        snap_path = snapshots_dir / f"v{version_number:03d}_{zmx_name}"
        shutil.copy2(zmx_source_path, snap_path)

        perf_dict = performance.model_dump(exclude_none=True) if performance else {}

        snapshot = DesignSnapshot(
            id=snapshot_id,
            project_id=project_id,
            version_number=version_number,
            snapshot_path=str(snap_path),
            zmx_path=str(Path(zmx_source_path).name),
            change_description=change_description,
            performance_metrics=perf_dict,
            session_id=session_id,
        )

        self._store.create_version(VersionRecord(
            id=snapshot.id, project_id=project_id,
            version_number=version_number,
            snapshot_path=str(snap_path),
            change_description=change_description,
            performance_metrics=perf_dict,
            session_id=session_id,
            created_at=snapshot.created_at,
        ))

        if performance:
            for metric_type, value in perf_dict.items():
                if value is not None:
                    self._store.save_performance_metric(PerformanceMetricRecord(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        version_id=snapshot_id,
                        metric_type=metric_type,
                        metric_data={"value": value},
                        created_at=snapshot.created_at,
                    ))

        logger.info("Snapshot v%d created for project %s", version_number, project_id[:8])
        return snapshot

    def list_snapshots(self, project_id: str) -> list[DesignSnapshot]:
        records = self._store.list_versions(project_id)
        return [self._record_to_snapshot(r) for r in records]

    def get_snapshot(self, version_id: str) -> Optional[DesignSnapshot]:
        record = self._store.get_version(version_id)
        if record is None:
            return None
        return self._record_to_snapshot(record)

    def rollback(self, project_id: str, version_id: str, zmx_target_path: str | Path) -> bool:
        snapshot = self.get_snapshot(version_id)
        if snapshot is None or snapshot.project_id != project_id:
            return False

        snap_path = Path(snapshot.snapshot_path)
        if not snap_path.exists():
            logger.error("Snapshot file not found: %s", snap_path)
            return False

        current_state = self.get_current_zmx_path(project_id)
        if current_state and Path(current_state).exists():
            self.create_snapshot(
                project_id=project_id,
                zmx_source_path=current_state,
                change_description=f"Auto-snapshot before rollback to v{snapshot.version_number}",
            )

        shutil.copy2(snap_path, zmx_target_path)
        logger.info("Rollback to v%d complete for project %s", snapshot.version_number, project_id[:8])
        return True

    def compare(self, version_id_a: str, version_id_b: str) -> dict[str, Any]:
        a = self.get_snapshot(version_id_a)
        b = self.get_snapshot(version_id_b)

        if a is None or b is None:
            return {}

        a_metrics = a.performance_metrics
        b_metrics = b.performance_metrics

        diffs = {}
        all_keys = set(a_metrics.keys()) | set(b_metrics.keys())
        for key in all_keys:
            va = a_metrics.get(key)
            vb = b_metrics.get(key)
            if va is not None and vb is not None and isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                diffs[key] = {
                    "version_a": va,
                    "version_b": vb,
                    "delta": round(vb - va, 6),
                    "delta_pct": round((vb - va) / max(abs(va), 1e-10) * 100, 2),
                }

        return {
            "version_a": {"number": a.version_number, "date": a.created_at, "desc": a.change_description},
            "version_b": {"number": b.version_number, "date": b.created_at, "desc": b.change_description},
            "diffs": diffs,
        }

    def get_performance_trend(self, project_id: str) -> list[dict[str, Any]]:
        snapshots = self.list_snapshots(project_id)
        trend = []
        for snap in sorted(snapshots, key=lambda s: s.version_number):
            trend.append({
                "version_number": snap.version_number,
                "created_at": snap.created_at,
                "metrics": snap.performance_metrics,
            })
        return trend

    def get_current_zmx_path(self, project_id: str) -> Optional[str]:
        record = self._store.get_project(project_id)
        return record.zmx_path if record else None

    def _record_to_snapshot(self, record: VersionRecord) -> DesignSnapshot:
        return DesignSnapshot(
            id=record.id,
            project_id=record.project_id,
            version_number=record.version_number,
            snapshot_path=record.snapshot_path,
            change_description=record.change_description,
            performance_metrics=record.performance_metrics,
            session_id=record.session_id,
            created_at=record.created_at,
        )
