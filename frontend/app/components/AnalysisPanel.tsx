"use client";

import { BarChart3 } from "lucide-react";

export default function AnalysisPanel() {
  return (
    <div className="panel-box">
      <div className="panel-hdr">
        <BarChart3 size={14} style={{ color: "var(--success)" }} />
        <h3>分析结果</h3>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <button className="btn btn-secondary btn-sm">MTF</button>
          <button className="btn btn-secondary btn-sm">点列图</button>
          <button className="btn btn-secondary btn-sm">波前</button>
        </div>
      </div>
      <div className="panel-body">
        <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-tertiary)" }}>
          <BarChart3 size={36} style={{ opacity: 0.15, marginBottom: 12 }} />
          <p style={{ fontSize: 12 }}>运行分析后图表将在此展示</p>
          <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 16 }}>
            <button className="btn btn-secondary btn-sm">MTF 分析</button>
            <button className="btn btn-secondary btn-sm">点列图</button>
            <button className="btn btn-secondary btn-sm">波前分析</button>
          </div>
        </div>
      </div>
    </div>
  );
}
