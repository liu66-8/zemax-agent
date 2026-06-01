import { useState, useEffect } from "react";
import { useProjectStore } from "@/stores";
import { invokeIPC } from "@/services/ipc";
import { Plus, FolderOpen } from "lucide-react";

interface Props { onSelect: () => void }

export default function ProjectExplorer({ onSelect }: Props) {
  const { projects, setProjects, setCurrent, currentProject } = useProjectStore();
  const [showingCreate, setShowingCreate] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  useEffect(() => {
    invokeIPC("list_projects").then((data: any) => {
      if (data) setProjects(Array.isArray(data) ? data : []);
    }).catch(() => {});
  }, []);

  const create = async () => {
    if (!name.trim()) return;
    await invokeIPC("create_project", { name, description: desc });
    setName(""); setDesc(""); setShowingCreate(false);
    const data: any = await invokeIPC("list_projects").catch(() => []);
    if (data) setProjects(Array.isArray(data) ? data : []);
  };

  const openProject = (id: string) => {
    onSelect();
    const p = projects.find((p: any) => p.id === id);
    if (p) setCurrent(p);
  };

  const phaseLabels: Record<string, string> = {
    requirements: "需求分析", initial_structure: "初始结构",
    optimization: "优化中", analysis: "分析中", tolerance: "容差分析", report: "报告",
  };

  return (
    <div className="panel">
      <div className="flex-between mb-16">
        <h2>项目管理</h2>
        <button className="btn btn-primary" onClick={() => setShowingCreate(!showingCreate)}>
          <Plus size={15} /> {showingCreate ? "取消" : "新建项目"}
        </button>
      </div>

      {showingCreate && (
        <div className="card" style={{ marginBottom: 20, borderColor: "var(--accent)", background: "var(--accent-soft)" }}>
          <input className="input" placeholder="项目名称" value={name}
            onChange={(e) => setName(e.target.value)} autoFocus style={{ marginBottom: 10 }} />
          <input className="input" placeholder="项目描述（选填）" value={desc}
            onChange={(e) => setDesc(e.target.value)} style={{ marginBottom: 12 }} />
          <button className="btn btn-primary" onClick={create} style={{ width: "100%" }}>
            创建项目
          </button>
        </div>
      )}

      {projects.length === 0 && !showingCreate ? (
        <div className="empty-state">
          <FolderOpen size={48} />
          <p>暂无项目<br />点击上方"新建项目"开始设计</p>
        </div>
      ) : (
        projects.map((p: any) => (
          <div key={p.id} className="card" onClick={() => openProject(p.id)}
            style={{
              cursor: "pointer", marginBottom: 8,
              background: currentProject?.id === p.id ? "var(--accent-soft)" : undefined,
              borderColor: currentProject?.id === p.id ? "var(--accent)" : undefined,
            }}>
            <div className="flex-between">
              <div style={{ fontWeight: 500, fontSize: 14 }}>{p.name}</div>
              <span className="badge" style={{ background: "var(--bg-hover)", color: "var(--text-secondary)" }}>
                {phaseLabels[p.design_phase] || p.design_phase || "新建"}
              </span>
            </div>
            <div style={{ fontSize: 11.5, color: "var(--text-tertiary)", marginTop: 6 }}>
              {p.system_type || "未指定类型"} · {p.description?.slice(0, 60) || "无描述"}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
