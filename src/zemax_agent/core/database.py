from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional

from pydantic import BaseModel, Field


SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    system_type TEXT DEFAULT '',
    design_phase TEXT DEFAULT 'requirements',
    tags TEXT DEFAULT '[]',
    workspace_path TEXT NOT NULL,
    zmx_path TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived_at TEXT,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    task_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    params TEXT DEFAULT '{}',
    progress REAL DEFAULT 0.0,
    result TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS versions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    version_number INTEGER NOT NULL,
    snapshot_path TEXT NOT NULL,
    change_description TEXT DEFAULT '',
    performance_metrics TEXT DEFAULT '{}',
    session_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT DEFAULT '',
    thread_id TEXT NOT NULL,
    messages TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT REFERENCES projects(id),
    session_id TEXT REFERENCES sessions(id),
    tool_name TEXT NOT NULL,
    caller TEXT DEFAULT 'user',
    params TEXT DEFAULT '{}',
    result TEXT,
    duration_ms REAL,
    error TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_prefs (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    version_id TEXT REFERENCES versions(id),
    metric_type TEXT NOT NULL,
    metric_data TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_versions_project ON versions(project_id);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_project ON operation_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_session ON operation_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_project ON performance_metrics(project_id);
"""


class ProjectRecord(BaseModel):
    id: str
    name: str
    description: str = ""
    system_type: str = ""
    design_phase: str = "requirements"
    tags: list[str] = Field(default_factory=list)
    workspace_path: str
    zmx_path: str = ""
    created_at: str
    updated_at: str
    archived_at: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskRecord(BaseModel):
    id: str
    project_id: str
    task_type: str
    status: str = "pending"
    params: dict[str, Any] = Field(default_factory=dict)
    progress: float = 0.0
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class VersionRecord(BaseModel):
    id: str
    project_id: str
    version_number: int
    snapshot_path: str
    change_description: str = ""
    performance_metrics: dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    created_at: str


class SessionRecord(BaseModel):
    id: str
    project_id: str
    title: str = ""
    thread_id: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str
    updated_at: str


class OperationLogRecord(BaseModel):
    id: Optional[int] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    tool_name: str
    caller: str = "user"
    params: dict[str, Any] = Field(default_factory=dict)
    result: Optional[dict[str, Any]] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    created_at: str


class PreferenceRecord(BaseModel):
    key: str
    value: str
    updated_at: str


class PerformanceMetricRecord(BaseModel):
    id: str
    project_id: str
    version_id: Optional[str] = None
    metric_type: str
    metric_data: dict[str, Any]
    created_at: str


class SQLiteStore:
    def __init__(self, db_path: str | Path = "zemax_agent.db"):
        self._db_path = Path(db_path)
        self._local = threading.local()
        self._init_db()

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript(SCHEMA_SQL)
            cursor = conn.execute("SELECT version FROM schema_version")
            row = cursor.fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (SCHEMA_VERSION,),
                )
            conn.commit()

    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = getattr(self._local, "conn", None)
        created = conn is None
        if created:
            conn = sqlite3.connect(str(self._db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn = conn
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn:
            conn.close()
            self._local.conn = None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _dict_to_row(self, data: dict) -> dict:
        return {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in data.items()}

    def _row_to_dict(self, row: dict) -> dict:
        result = {}
        json_fields = {"tags", "params", "result", "error", "metadata",
                       "performance_metrics", "messages", "metric_data"}
        for k, v in row.items():
            if k in json_fields and isinstance(v, str):
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            else:
                result[k] = v
        return result

    # --- Project CRUD ---

    def create_project(self, record: ProjectRecord) -> ProjectRecord:
        data = record.model_dump()
        data["tags"] = json.dumps(data.get("tags", []))
        data["metadata"] = json.dumps(data.get("metadata", {}))
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO projects (id, name, description, system_type, design_phase,
                   tags, workspace_path, zmx_path, created_at, updated_at, archived_at, metadata)
                   VALUES (:id, :name, :description, :system_type, :design_phase,
                   :tags, :workspace_path, :zmx_path, :created_at, :updated_at, :archived_at, :metadata)""",
                data,
            )
        return record

    def get_project(self, project_id: str) -> Optional[ProjectRecord]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            return None
        return ProjectRecord(**self._row_to_dict(dict(row)))

    def list_projects(self, archived: bool = False, tag: Optional[str] = None) -> list[ProjectRecord]:
        query = "SELECT * FROM projects WHERE archived_at IS " + ("NOT NULL" if archived else "NULL")
        params: list[Any] = []
        if tag:
            query += " AND tags LIKE ?"
            params.append(f'%"{tag}"%')
        query += " ORDER BY updated_at DESC"
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [ProjectRecord(**self._row_to_dict(dict(r))) for r in rows]

    def update_project(self, project_id: str, **kwargs: Any) -> Optional[ProjectRecord]:
        if not kwargs:
            return self.get_project(project_id)
        kwargs["updated_at"] = self._now()
        set_clause = ", ".join(f"{k}=:{k}" for k in kwargs)
        with self._get_conn() as conn:
            cursor = conn.execute(
                f"UPDATE projects SET {set_clause} WHERE id=:id",
                {"id": project_id, **kwargs},
            )
        if cursor.rowcount == 0:
            return None
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cursor.rowcount > 0

    def archive_project(self, project_id: str) -> Optional[ProjectRecord]:
        return self.update_project(project_id, archived_at=self._now())

    def unarchive_project(self, project_id: str) -> Optional[ProjectRecord]:
        return self.update_project(project_id, archived_at=None)

    # --- Task CRUD ---

    def create_task(self, record: TaskRecord) -> TaskRecord:
        data = record.model_dump()
        data["params"] = json.dumps(data.get("params", {}))
        data["result"] = json.dumps(data["result"]) if data.get("result") else None
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO tasks (id, project_id, task_type, status, params,
                   progress, result, error, created_at, started_at, completed_at)
                   VALUES (:id, :project_id, :task_type, :status, :params,
                   :progress, :result, :error, :created_at, :started_at, :completed_at)""",
                data,
            )
        return record

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        return TaskRecord(**self._row_to_dict(dict(row)))

    def list_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[TaskRecord]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [TaskRecord(**self._row_to_dict(dict(r))) for r in rows]

    def update_task(self, task_id: str, **kwargs: Any) -> Optional[TaskRecord]:
        if not kwargs:
            return self.get_task(task_id)
        jsonify_fields = {"params", "result", "error"}
        for field in jsonify_fields:
            if field in kwargs and isinstance(kwargs[field], (dict, list)):
                kwargs[field] = json.dumps(kwargs[field])
        set_clause = ", ".join(f"{k}=:{k}" for k in kwargs)
        with self._get_conn() as conn:
            cursor = conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE id=:id",
                {"id": task_id, **kwargs},
            )
        if cursor.rowcount == 0:
            return None
        return self.get_task(task_id)

    # --- Version CRUD ---

    def create_version(self, record: VersionRecord) -> VersionRecord:
        data = record.model_dump()
        data["performance_metrics"] = json.dumps(data.get("performance_metrics", {}))
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO versions (id, project_id, version_number, snapshot_path,
                   change_description, performance_metrics, session_id, created_at)
                   VALUES (:id, :project_id, :version_number, :snapshot_path,
                   :change_description, :performance_metrics, :session_id, :created_at)""",
                data,
            )
        return record

    def get_version(self, version_id: str) -> Optional[VersionRecord]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM versions WHERE id = ?", (version_id,)).fetchone()
        if row is None:
            return None
        return VersionRecord(**self._row_to_dict(dict(row)))

    def list_versions(self, project_id: str) -> list[VersionRecord]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM versions WHERE project_id = ? ORDER BY version_number DESC",
                (project_id,),
            ).fetchall()
        return [VersionRecord(**self._row_to_dict(dict(r))) for r in rows]

    def delete_version(self, version_id: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM versions WHERE id = ?", (version_id,))
        return cursor.rowcount > 0

    # --- Session CRUD ---

    def create_session(self, record: SessionRecord) -> SessionRecord:
        data = record.model_dump()
        data["messages"] = json.dumps(data.get("messages", []))
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO sessions (id, project_id, title, thread_id, messages,
                   created_at, updated_at)
                   VALUES (:id, :project_id, :title, :thread_id, :messages,
                   :created_at, :updated_at)""",
                data,
            )
        return record

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            return None
        return SessionRecord(**self._row_to_dict(dict(row)))

    def list_sessions(self, project_id: str) -> list[SessionRecord]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE project_id = ? ORDER BY updated_at DESC",
                (project_id,),
            ).fetchall()
        return [SessionRecord(**self._row_to_dict(dict(r))) for r in rows]

    def update_session(self, session_id: str, **kwargs: Any) -> Optional[SessionRecord]:
        if not kwargs:
            return self.get_session(session_id)
        kwargs["updated_at"] = self._now()
        if "messages" in kwargs and isinstance(kwargs["messages"], list):
            kwargs["messages"] = json.dumps(kwargs["messages"])
        set_clause = ", ".join(f"{k}=:{k}" for k in kwargs)
        with self._get_conn() as conn:
            cursor = conn.execute(
                f"UPDATE sessions SET {set_clause} WHERE id=:id",
                {"id": session_id, **kwargs},
            )
        if cursor.rowcount == 0:
            return None
        return self.get_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cursor.rowcount > 0

    # --- Operation Log CRUD ---

    def log_operation(self, record: OperationLogRecord) -> int:
        data = record.model_dump(exclude={"id"})
        data["params"] = json.dumps(data.get("params", {}))
        data["result"] = json.dumps(data["result"]) if data.get("result") else None
        with self._get_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO operation_logs (project_id, session_id, tool_name, caller,
                   params, result, duration_ms, error, created_at)
                   VALUES (:project_id, :session_id, :tool_name, :caller,
                   :params, :result, :duration_ms, :error, :created_at)""",
                data,
            )
            return cursor.lastrowid or 0

    def list_operation_logs(
        self,
        project_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[OperationLogRecord]:
        query = "SELECT * FROM operation_logs WHERE 1=1"
        params: list[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [OperationLogRecord(**self._row_to_dict(dict(r))) for r in rows]

    # --- User Preferences ---

    def set_preference(self, key: str, value: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO user_prefs (key, value, updated_at)
                   VALUES (?, ?, ?)""",
                (key, value, self._now()),
            )

    def get_preference(self, key: str) -> Optional[str]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT value FROM user_prefs WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def get_all_preferences(self) -> dict[str, str]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM user_prefs").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def delete_preference(self, key: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM user_prefs WHERE key = ?", (key,))
        return cursor.rowcount > 0

    # --- Performance Metrics ---

    def save_performance_metric(self, record: PerformanceMetricRecord) -> PerformanceMetricRecord:
        data = record.model_dump()
        data["metric_data"] = json.dumps(data["metric_data"])
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO performance_metrics (id, project_id, version_id,
                   metric_type, metric_data, created_at)
                   VALUES (:id, :project_id, :version_id, :metric_type, :metric_data, :created_at)""",
                data,
            )
        return record

    def list_performance_metrics(
        self, project_id: str, version_id: Optional[str] = None
    ) -> list[PerformanceMetricRecord]:
        query = "SELECT * FROM performance_metrics WHERE project_id = ?"
        params: list[Any] = [project_id]
        if version_id:
            query += " AND version_id = ?"
            params.append(version_id)
        query += " ORDER BY created_at DESC"
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [PerformanceMetricRecord(**self._row_to_dict(dict(r))) for r in rows]

    # --- Schema Migration ---

    def get_schema_version(self) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT version FROM schema_version").fetchone()
        return row["version"] if row else 0

    def migrate(self, target_version: Optional[int] = None) -> int:
        current = self.get_schema_version()
        target = target_version or SCHEMA_VERSION
        if current >= target:
            return current
        with self._get_conn() as conn:
            for version in range(current + 1, target + 1):
                self._run_migration(conn, version)
                conn.execute(
                    "UPDATE schema_version SET version = ?", (version,)
                )
            conn.commit()
        return target

    def _run_migration(self, conn: sqlite3.Connection, version: int) -> None:
        pass
