import { useState } from "react";
import { useProjectStore } from "@/stores";
import { invokeIPC } from "@/services/ipc";

interface Props { onSelect: (id: string) => void }

export default function ProjectExplorer({ onSelect }: Props) {
  const { projects, setProjects, setCurrent, currentProject } = useProjectStore();
  const [showingCreate, setShowingCreate] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  const loadProjects = async () => {
    try {
      const data = await invokeIPC("list_projects") as any[];
      if (data) setProjects(data.map((p: any) => p));
    } catch { /* mock */ }
  };

  useState(() => { loadProjects(); });

  const create = async () => {
    if (!name) return;
    await invokeIPC("create_project", { name, description: desc });
    setName(""); setDesc(""); setShowingCreate(false);
    loadProjects();
  };

  const openProject = (id: string) => {
    onSelect(id);
    const p = projects.find((p: any) => p.id === id);
    if (p) setCurrent(p);
  };

  return (
    <div className="space-y-4" style={{ padding: "4px 0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ fontSize: 16, margin: 0 }}>项目管理</h2>
        <button onClick={() => setShowingCreate(!showingCreate)} style={btnStyle}>
          {showingCreate ? "取消" : "+ 新建"}
        </button>
      </div>

      {showingCreate && (
        <div style={{ background: "var(--bg-tertiary)", padding: 12, borderRadius: 6, marginBottom: 12 }}>
          <input placeholder="项目名称" value={name} onChange={(e) => setName(e.target.value)}
            style={inputStyle} autoFocus />
          <input placeholder="项目描述" value={desc} onChange={(e) => setDesc(e.target.value)}
            style={{ ...inputStyle, marginTop: 8 }} />
          <button onClick={create} style={{ ...btnStyle, marginTop: 8, width: "100%" }}>创建项目</button>
        </div>
      )}

      {projects.length === 0 && (
        <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>暂无项目，点击"新建"开始设计。</p>
      )}

      {projects.map((p: any) => (
        <div key={p.id}
          onClick={() => openProject(p.id)}
          style={{
            padding: "10px 12px", borderRadius: 6, cursor: "pointer", marginBottom: 4,
            background: currentProject?.id === p.id ? "var(--accent)" : "var(--bg-tertiary)",
            transition: "background 0.15s",
          }}>
          <div style={{ fontWeight: 500, fontSize: 14 }}>{p.name}</div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>
            {p.system_type || "新项目"} · {p.design_phase}
          </div>
        </div>
      ))}
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  padding: "6px 14px", background: "var(--accent)", border: "none",
  color: "#fff", borderRadius: 4, cursor: "pointer", fontSize: 13,
};

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "8px", background: "var(--bg-primary)", border: "1px solid var(--border)",
  borderRadius: 4, color: "var(--text-primary)", fontSize: 13, outline: "none",
};
