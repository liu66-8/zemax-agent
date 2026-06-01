"use client";

import Sidebar from "./components/Sidebar";
import ConnectionPanel from "./components/ConnectionPanel";
import DesignPanel from "./components/DesignPanel";
import AnalysisPanel from "./components/AnalysisPanel";
import AIPanel from "./components/AIPanel";
import FileManager from "./components/FileManager";
import SettingsModal from "./components/SettingsModal";

export default function Home() {
  return (
    <div className="app-shell">
      <Sidebar />

      <div className="main-area">
        <ConnectionPanel />

        <div className="panels-grid">
          <div className="panels-main">
            <DesignPanel />
            <AnalysisPanel />
          </div>
          <div className="panels-right">
            <AIPanel />
            <FileManager />
          </div>
        </div>
      </div>

      <SettingsModal />
    </div>
  );
}
