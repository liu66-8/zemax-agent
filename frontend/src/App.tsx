import { useState } from "react";
import ProjectExplorer from "./components/ProjectExplorer";
import AIChat from "./components/AIChat";
import DesignControl from "./components/DesignControl";
import TaskConsole from "./components/TaskConsole";

type Panel = "project" | "design" | "analysis" | "ai" | "tasks" | "versions" | "knowledge";

function App() {
  const [active, setActive] = useState<Panel>("project");
  const [connected, _setConnected] = useState(false);

  const panels: { key: Panel; label: string }[] = [
    { key: "project", label: "项目" },
    { key: "design", label: "设计" },
    { key: "analysis", label: "分析" },
    { key: "ai", label: "AI 助手" },
    { key: "tasks", label: "任务" },
    { key: "versions", label: "版本" },
    { key: "knowledge", label: "知识库" },
  ];

  const renderPanel = () => {
    switch (active) {
      case "project": return <ProjectExplorer onSelect={(id) => setActive("design")} />;
      case "design": return <DesignControl />;
      case "analysis": return <Placeholder title="分析结果" desc="MTF、点列图、波前分析等结果将在此展示。" />;
      case "ai": return <AIChat />;
      case "tasks": return <TaskConsole />;
      case "versions": return <Placeholder title="版本管理" desc="设计快照、版本对比和性能趋势将在此展示。" />;
      case "knowledge": return <Placeholder title="知识库" desc="搜索光学文档、设计案例和玻璃材料目录。" />;
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Zemax Agent</h1>
        <span className="app-subtitle">光学工程工作台</span>
        <div className="app-status">
          <span className={`status-dot ${connected ? "status-connected" : "status-disconnected"}`} />
          <span>{connected ? "OpticStudio 已连接" : "未连接"}</span>
        </div>
      </header>

      <nav className="app-nav">
        {panels.map((p) => (
          <button
            key={p.key}
            className={`nav-btn ${active === p.key ? "active" : ""}`}
            onClick={() => setActive(p.key)}
          >
            {p.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {renderPanel()}
      </main>

      <footer className="app-footer">
        <span>Zemax Agent v0.1.0</span>
        <span>{panels.find((p) => p.key === active)?.label} 面板</span>
      </footer>
    </div>
  );
}

function Placeholder({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="panel">
      <h2>{title}</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 8 }}>{desc}</p>
    </div>
  );
}

export default App;
