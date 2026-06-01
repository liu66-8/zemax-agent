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
    { key: "project", label: "Project" },
    { key: "design", label: "Design" },
    { key: "analysis", label: "Analysis" },
    { key: "ai", label: "AI Chat" },
    { key: "tasks", label: "Tasks" },
    { key: "versions", label: "Versions" },
    { key: "knowledge", label: "Knowledge" },
  ];

  const renderPanel = () => {
    switch (active) {
      case "project": return <ProjectExplorer onSelect={(id) => setActive("design")} />;
      case "design": return <DesignControl />;
      case "analysis": return <Placeholder title="Analysis Results" desc="MTF, spot diagrams, wavefront, and more will appear here." />;
      case "ai": return <AIChat />;
      case "tasks": return <TaskConsole />;
      case "versions": return <Placeholder title="Version Management" desc="Design snapshots, comparisons, and performance trends." />;
      case "knowledge": return <Placeholder title="Knowledge Base" desc="Search optical documentation, design cases, and glass catalogs." />;
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Zemax Agent</h1>
        <span className="app-subtitle">Optical Engineering Workspace</span>
        <div className="app-status">
          <span className={`status-dot ${connected ? "status-connected" : "status-disconnected"}`} />
          <span>{connected ? "OpticStudio" : "Disconnected"}</span>
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
        <span>{active.toUpperCase()} Panel</span>
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
