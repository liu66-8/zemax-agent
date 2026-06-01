"use client";

import Sidebar from "./components/Sidebar";
import DesignPanel from "./components/DesignPanel";
import AnalysisPanel from "./components/AnalysisPanel";
import AIPanel from "./components/AIPanel";
import TaskPanel from "./components/TaskPanel";

export default function Home() {
  return (
    <div className="app-shell">
      <Sidebar />

      <div className="main-area">
        <header className="topbar">
          <span className="topbar-title">仪表盘</span>
          <div className="topbar-status">
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div className="status-dot off" /> OpticStudio
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div className="status-dot off" /> Qdrant
            </span>
          </div>
        </header>

        <div className="panels-grid">
          <div className="panels-main">
            <DesignPanel />
            <AnalysisPanel />
          </div>
          <div className="panels-right">
            <AIPanel />
            <TaskPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
