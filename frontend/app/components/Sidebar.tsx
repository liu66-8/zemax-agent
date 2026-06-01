"use client";

import { useEffect } from "react";
import { FolderOpen, Plus, Clock, FileText, Zap, Database, Loader2 } from "lucide-react";
import { useProjectStore, useTaskStore, useConnectionStore, useFileStore, useDesignStore, useSettingsStore, type ProjectItem, type SurfaceData } from "@/app/stores";
import { useModal } from "@/app/components/Modal";
import { createTauriIPC } from "@/app/services/api";
import { useState } from "react";

const phaseLabels: Record<string, string> = {
  requirements: "需求", initial_structure: "初始结构",
  optimization: "优化", analysis: "分析", tolerance: "容差", report: "报告",
};

export default function Sidebar() {
  const { projects, current, setProjects, setCurrent, loading } = useProjectStore();
  const { tasks, setTasks } = useTaskStore();
  const { zos, qdrant, connectZOS, connectQdrant, setZOS, setQdrant, setPython } = useConnectionStore();
  const { recentFiles } = useFileStore();
  const { setLensData } = useDesignStore();
  const { open, close } = useModal();
  const { fetchSettings } = useSettingsStore();
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  useEffect(() => {
    const ipc = createTauriIPC();
    ipc.listProjects().then((data: any) => {
      if (Array.isArray(data) && data.length > 0) setProjects(data);
    }).catch(() => {});
    fetchSettings();
    connectZOS();
    connectQdrant();
  }, []);

  useEffect(() => {
    const ipc = createTauriIPC();
    ipc.getTasks().then((data: any) => {
      if (Array.isArray(data)) { setTasks(data); }
    }).catch(() => {});
    const interval = setInterval(() => {
      ipc.getTasks().then((data: any) => {
        if (Array.isArray(data)) setTasks(data);
      }).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleNewProject = async () => {
    if (!name.trim()) return;
    try {
      const ipc = createTauriIPC();
      const result = await ipc.createProject(name, desc);
      if (result) {
        const p: ProjectItem = {
          id: `proj-${Date.now()}`, name, description: desc,
          system_type: "", design_phase: "requirements", tags: [],
          created_at: new Date().toISOString(),
        };
        setProjects([p, ...projects]);
        setCurrent(p);
      }
    } catch { /* silent */ }
    setName(""); setDesc(""); close();
  };

  const loadDesign = async () => {
    const ipc = createTauriIPC();
    const data: any = await ipc.getLensData();
    if (data && data.surfaces) {
      setLensData(
        data.surfaces as SurfaceData[],
        data.effective_focal_length || 0,
        data.f_number || 0,
        data.total_track || 0,
      );
    }
  };

  const selectProject = (p: ProjectItem) => {
    setCurrent(p);
    loadDesign();
  };

  const openNewModal = () => open(
    <div>
      <h2>新建项目</h2>
      <input className="input" placeholder="项目名称" value={name}
        onChange={(e) => setName(e.target.value)} autoFocus style={{ marginBottom: 10 }} />
      <input className="input" placeholder="项目描述（选填）" value={desc}
        onChange={(e) => setDesc(e.target.value)} />
      <div className="modal-actions">
        <button className="btn btn-secondary" onClick={close}>取消</button>
        <button className="btn btn-primary" onClick={handleNewProject}>创建</button>
      </div>
    </div>
  );

  return (
    <aside className="sidebar">
      <div className="sidebar-section" style={{ padding: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <div style={{ width: 26, height: 26, background: "linear-gradient(135deg, var(--accent), var(--purple))", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 700, fontSize: 13 }}>Z</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Zemax Agent</div>
          </div>
        </div>
      </div>

      <div className="sidebar-section">
        <h3>连接状态</h3>
        <div style={{ display: "flex", gap: 12, marginTop: 4 }}>
          <ConnItem icon={Zap} label="ZOS" status={zos.status} />
          <ConnItem icon={Database} label="Qdrant" status={qdrant.status} />
        </div>
      </div>

      <div className="sidebar-section">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <h3>项目</h3>
          <button className="btn btn-primary btn-sm" onClick={openNewModal}><Plus size={13} /></button>
        </div>
        {loading ? (
          <div style={{ textAlign: "center", padding: "16px 0" }}><Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} /></div>
        ) : projects.length === 0 ? (
          <div style={{ textAlign: "center", padding: "20px 0", color: "var(--text-tertiary)", fontSize: 12 }}>
            <FolderOpen size={24} style={{ opacity: 0.3, marginBottom: 6 }} /><p>暂无项目</p>
          </div>
        ) : (
          projects.map((p) => (
            <div key={p.id} className={`card ${current?.id === p.id ? "active" : ""}`}
              onClick={() => selectProject(p)}
              style={{ cursor: "pointer", marginBottom: 6 }}>
              <div style={{ fontWeight: 500, fontSize: 13 }}>{p.name}</div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: 11, color: "var(--text-tertiary)" }}>
                <span>{p.system_type || "新项目"}</span>
                <span className="badge" style={{ background: "var(--bg-hover)", color: "var(--text-secondary)" }}>
                  {phaseLabels[p.design_phase] || p.design_phase}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-section">
        <h3>最近文件</h3>
        {recentFiles.length === 0 ? (
          <p style={{ fontSize: 11.5, color: "var(--text-tertiary)", padding: "8px 0" }}>暂无打开记录</p>
        ) : (
          recentFiles.slice(0, 4).map((f) => (
            <div key={f.path} style={{ padding: "5px 0", fontSize: 11.5, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}
              onClick={loadDesign}>
              <FileText size={11} style={{ opacity: 0.4 }} />
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.name}</span>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-section">
        <h3>任务</h3>
        {tasks.length === 0 ? (
          <div style={{ textAlign: "center", padding: "14px 0", color: "var(--text-tertiary)", fontSize: 12 }}>
            <Clock size={18} style={{ opacity: 0.3, marginBottom: 3 }} /><p>暂无任务</p>
          </div>
        ) : (
          tasks.slice(0, 5).map((t) => {
            const colors: Record<string, string> = { pending: "var(--warning)", running: "var(--accent)", completed: "var(--success)", failed: "var(--error)" };
            const labels: Record<string, string> = { pending: "等待", running: "执行", completed: "完成", failed: "失败" };
            return (
              <div key={t.id} style={{ padding: "5px 0", fontSize: 11.5, display: "flex", justifyContent: "space-between" }}>
                <span>{t.task_type}</span>
                <span style={{ color: colors[t.status] || "var(--text-tertiary)" }}>{labels[t.status] || t.status}</span>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}

function ConnItem({ icon: Icon, label, status }: { icon: any; label: string; status: string }) {
  const colors: Record<string, string> = { connected: "var(--success)", disconnected: "var(--error)", connecting: "var(--warning)", error: "var(--error)" };
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11 }}>
      <div style={{ width: 6, height: 6, borderRadius: "50%", background: colors[status] || "var(--text-tertiary)", flexShrink: 0 }} />
      <Icon size={10} />
      <span>{label}</span>
    </div>
  );
}
