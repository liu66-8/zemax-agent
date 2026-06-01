"use client";

import { Undo2, Redo2, Gauge } from "lucide-react";
import { useDesignStore } from "@/app/stores";
import { useModal, ConfirmDialog } from "@/app/components/Modal";

export default function DesignPanel() {
  const { surfaces, efl, fNumber, totalTrack, undo, redo } = useDesignStore();
  const { open, close } = useModal();

  const confirmUndo = () => open(
    <ConfirmDialog title="撤销操作" message="确定要撤销上一步镜头编辑操作吗？"
      onConfirm={() => { undo(); close(); }} onCancel={close} />
  );

  return (
    <div className="panel-box">
      <div className="panel-hdr">
        <Gauge size={14} style={{ color: "var(--accent)" }} />
        <h3>设计控制</h3>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <button className="btn btn-secondary btn-sm" onClick={confirmUndo}><Undo2 size={12} /></button>
          <button className="btn btn-secondary btn-sm" onClick={redo}><Redo2 size={12} /></button>
        </div>
      </div>
      <div className="panel-body">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 12 }}>
          <MetricCard label="有效焦距" value={`${efl.toFixed(1)} mm`} />
          <MetricCard label="F 数" value={fNumber.toFixed(1)} />
          <MetricCard label="总长度" value={`${totalTrack.toFixed(1)} mm`} />
        </div>
        {surfaces.length === 0 ? (
          <div style={{ textAlign: "center", padding: "28px 0", color: "var(--text-tertiary)", fontSize: 12 }}>
            <Gauge size={28} style={{ opacity: 0.2, marginBottom: 6 }} />
            <p>加载 ZMX 文件以查看镜头数据</p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead><tr><th>#</th><th>面型</th><th>曲率半径</th><th>厚度</th><th>玻璃</th><th>半口径</th></tr></thead>
              <tbody>
                {surfaces.map((s) => (
                  <tr key={s.index} className={s.is_stop ? "stop-row" : ""}>
                    <td>{s.index}{s.is_stop ? " ⏺" : ""}</td>
                    <td style={{ fontWeight: 500 }}>{s.surf_type}</td>
                    <td>{s.radius === 0 ? "∞" : s.radius.toFixed(3)}</td>
                    <td>{s.thickness.toFixed(3)}</td>
                    <td>{s.glass || "—"}</td>
                    <td>{s.semi_diameter.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card" style={{ textAlign: "center", padding: "10px 8px" }}>
      <div style={{ color: "var(--text-tertiary)", fontSize: 10 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 700, marginTop: 2 }}>{value}</div>
    </div>
  );
}
