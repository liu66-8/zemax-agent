"use client";

import { useState, useEffect } from "react";
import { FolderOpen, Plus, Clock } from "lucide-react";
import { useProjectStore, useTaskStore, type ProjectItem } from "@/app/stores";
import { useModal, ConfirmDialog } from "@/app/components/Modal";

export default function Sidebar() {
  const { projects, current, setProjects, setCurrent } = useProjectStore();
  const { tasks } = useTaskStore();
  const { open, close } = useModal();
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  useEffect(() => {
    Promise.resolve([
      { id: "demo-1", name: "Cooke Triplet f/4 100mm", description: "标准三片式镜头设计", system_type: "Cooke Triplet", design_phase: "optimization", tags: [], created_at: "2025-06-01" },
      { id: "demo-2", name: "Double Gauss f/2 50mm", description: "大光圈双高斯设计", system_type: "Double Gauss", design_phase: "initial_structure", tags: [], created_at: "2025-06-02" },
    ]).then(setProjects);
  }, []);

  const phaseLabels: Record<string, string> = {
    requirements: "需求", initial_structure: "初始结构",
    optimization: "优化", analysis: "分析", tolerance: "容差", report: "报告",
  };

  const handleNewProject = () => {
    if (!name.trim()) return;
    const p: ProjectItem = {
      id: `proj-${Date.now()}`, name, description: desc,
      system_type: "", design_phase: "requirements", tags: [], created_at: new Date().toISOString(),
    };
    setProjects([p, ...projects]);
    setCurrent(p);
    setName(""); setDesc("");
    close();
  };

  const openNewModal = () => open(
    <div>
      <h2>新建项目</h2>
      <input className="input" placeholder="项目名称" value={name}
        onChange={(e) => setName(e.target.value)} autoFocus
        style={{ marginBottom: 10 }} />
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
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <div style={{ width: 26, height: 26, background: "linear-gradient(135deg, var(--accent), var(--purple))", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 700, fontSize: 13 }}>Z</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Zemax Agent</div>
            <div style={{ fontSize: 10, color: "var(--text-tertiary)" }}>光学工程工作台</div>
          </div>
        </div>
      </div>

      <div className="sidebar-section">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <h3>项目</h3>
          <button className="btn btn-primary btn-sm" onClick={openNewModal}><Plus size={13} /></button>
        </div>
        {projects.length === 0 ? (
          <div style={{ textAlign: "center", padding: "24px 0", color: "var(--text-tertiary)", fontSize: 12 }}>
            <FolderOpen size={28} style={{ opacity: 0.3, marginBottom: 8 }} />
            <p>暂无项目</p>
          </div>
        ) : (
          projects.map((p) => (
            <div key={p.id} className={`card ${current?.id === p.id ? "active" : ""}`}
              onClick={() => setCurrent(p)} style={{ cursor: "pointer", marginBottom: 6 }}>
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
        <h3>任务</h3>
        {tasks.length === 0 ? (
          <div style={{ textAlign: "center", padding: "16px 0", color: "var(--text-tertiary)", fontSize: 12 }}>
            <Clock size={20} style={{ opacity: 0.3, marginBottom: 4 }} />
            <p>暂无任务</p>
          </div>
        ) : (
          tasks.slice(0, 5).map((t) => {
            const colors: Record<string, string> = { pending: "var(--warning)", running: "var(--accent)", completed: "var(--success)", failed: "var(--error)" };
            const labels: Record<string, string> = { pending: "等待", running: "执行", completed: "完成", failed: "失败" };
            return (
              <div key={t.id} style={{ padding: "6px 0", fontSize: 12, display: "flex", justifyContent: "space-between" }}>
                <span>{t.task_type}</span>
                <span style={{ color: colors[t.status] || "var(--text-tertiary)", fontSize: 11 }}>{labels[t.status] || t.status}</span>
              </div>
            );
          })
        )}
      </div>

      <div className="sidebar-section" style={{ marginTop: "auto" }}>
        <div className="status-dot off" style={{ display: "inline-block", marginRight: 6 }} />
        <span style={{ fontSize: 11.5, color: "var(--text-secondary)" }}>OpticStudio 未连接</span>
      </div>
    </aside>
  );
}
