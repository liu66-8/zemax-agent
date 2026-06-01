import { useState } from "react";

type Panel = "project" | "design" | "analysis" | "ai" | "tasks" | "versions" | "knowledge";

function App() {
  const [active, setActive] = useState<Panel>("project");

  const panels: { key: Panel; label: string }[] = [
    { key: "project", label: "Project" },
    { key: "design", label: "Design" },
    { key: "analysis", label: "Analysis" },
    { key: "ai", label: "AI Chat" },
    { key: "tasks", label: "Tasks" },
    { key: "versions", label: "Versions" },
    { key: "knowledge", label: "Knowledge" },
  ];

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Zemax Agent</h1>
        <span className="app-subtitle">Optical Engineering Workspace</span>
        <div className="app-status">
          <span className="status-dot status-disconnected" />
          <span>OpticStudio</span>
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
        <div className="panel">
          <h2>{panels.find((p) => p.key === active)?.label}</h2>
          <p>Ready for optical design tasks.</p>
        </div>
      </main>

      <footer className="app-footer">
        <span>Zemax Agent v0.1.0</span>
        <span>Status: Idle</span>
      </footer>
    </div>
  );
}

export default App;
