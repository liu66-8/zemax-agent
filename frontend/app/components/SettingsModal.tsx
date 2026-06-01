"use client";

import { useSettingsStore } from "@/app/stores";
import { X } from "lucide-react";

export default function SettingsModal() {
  const { settings, update, showSettings, setShowSettings } = useSettingsStore();
  if (!showSettings) return null;

  return (
    <div className="modal-overlay" onClick={() => setShowSettings(false)}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()} style={{ minWidth: 520 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h2 style={{ margin: 0 }}>系统设置</h2>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowSettings(false)}><X size={16} /></button>
        </div>

        <h3 style={{ fontSize: 13, color: "var(--accent)", marginBottom: 12, marginTop: 16 }}>Zemax OpticStudio</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <div>
            <label style={{ fontSize: 11, color: "var(--text-tertiary)", display: "block", marginBottom: 4 }}>连接模式</label>
            <select className="input" value={settings.zosMode}
              onChange={(e) => update({ zosMode: e.target.value as "standalone" | "extension" })}>
              <option value="standalone">Standalone (独立)</option>
              <option value="extension">Extension (扩展)</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: 11, color: "var(--text-tertiary)", display: "block", marginBottom: 4 }}>连接超时 (秒)</label>
            <input className="input" type="number" value={settings.zosTimeout}
              onChange={(e) => update({ zosTimeout: Number(e.target.value) })} />
          </div>
        </div>

        <h3 style={{ fontSize: 13, color: "var(--accent)", marginBottom: 12, marginTop: 16 }}>Qdrant 向量存储</h3>
        <div>
          <label style={{ fontSize: 11, color: "var(--text-tertiary)", display: "block", marginBottom: 4 }}>服务器地址</label>
          <input className="input" value={settings.qdrantUrl}
            onChange={(e) => update({ qdrantUrl: e.target.value })} />
        </div>

        <h3 style={{ fontSize: 13, color: "var(--accent)", marginBottom: 12, marginTop: 16 }}>LLM 大语言模型</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <div>
            <label style={{ fontSize: 11, color: "var(--text-tertiary)", display: "block", marginBottom: 4 }}>提供商</label>
            <input className="input" value={settings.llmProvider}
              onChange={(e) => update({ llmProvider: e.target.value })} />
          </div>
          <div>
            <label style={{ fontSize: 11, color: "var(--text-tertiary)", display: "block", marginBottom: 4 }}>模型</label>
            <input className="input" value={settings.llmModel}
              onChange={(e) => update({ llmModel: e.target.value })} />
          </div>
        </div>
        <div style={{ marginTop: 10 }}>
          <label style={{ fontSize: 11, color: "var(--text-tertiary)", display: "block", marginBottom: 4 }}>API Base URL</label>
          <input className="input" value={settings.llmApiBase}
            onChange={(e) => update({ llmApiBase: e.target.value })} />
        </div>

        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={() => setShowSettings(false)}>取消</button>
          <button className="btn btn-primary" onClick={() => setShowSettings(false)}>保存设置</button>
        </div>
      </div>
    </div>
  );
}
