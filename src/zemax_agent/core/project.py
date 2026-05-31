from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class DesignPhase(str, Enum):
    REQUIREMENTS = "requirements"
    INITIAL_STRUCTURE = "initial_structure"
    OPTIMIZATION = "optimization"
    ANALYSIS = "analysis"
    TOLERANCE = "tolerance"
    REPORT = "report"


class ProjectMeta(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    system_type: str = ""
    design_phase: DesignPhase = DesignPhase.REQUIREMENTS
    tags: list[str] = Field(default_factory=list)
    workspace_path: str = ""
    zmx_path: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    archived_at: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectWorkspace:
    SUBDIRS = ["designs", "analyses", "reports", "snapshots", "sessions"]
    MANIFEST = "project.json"

    def __init__(self, root_dir: str | Path):
        self._root = Path(root_dir).resolve()

    @property
    def root(self) -> Path:
        return self._root

    @property
    def designs_dir(self) -> Path:
        return self._root / "designs"

    @property
    def analyses_dir(self) -> Path:
        return self._root / "analyses"

    @property
    def reports_dir(self) -> Path:
        return self._root / "reports"

    @property
    def snapshots_dir(self) -> Path:
        return self._root / "snapshots"

    @property
    def sessions_dir(self) -> Path:
        return self._root / "sessions"

    def initialize(self) -> None:
        for subdir in self.SUBDIRS:
            (self._root / subdir).mkdir(parents=True, exist_ok=True)

    def save_manifest(self, meta: ProjectMeta) -> None:
        data = meta.model_dump(mode="json")
        with open(self._root / self.MANIFEST, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_manifest(cls, root_dir: str | Path) -> ProjectMeta:
        manifest_path = Path(root_dir) / cls.MANIFEST
        if not manifest_path.exists():
            raise FileNotFoundError(f"Project manifest not found: {manifest_path}")
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProjectMeta.model_validate(data)

    def list_files(self, subdir: str, pattern: str = "*") -> list[Path]:
        target = self._root / subdir
        if not target.exists():
            return []
        return sorted(target.glob(pattern))

    def export_to_zip(self, output_path: str | Path) -> Path:
        output = Path(output_path).with_suffix(".zip")
        base = shutil.make_archive(str(output.with_suffix("")), "zip", self._root)
        shutil.move(base, output)
        return output

    @classmethod
    def import_from_zip(cls, zip_path: str | Path, target_dir: str | Path) -> "ProjectWorkspace":
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(str(zip_path), str(target), "zip")
        return cls(target)
