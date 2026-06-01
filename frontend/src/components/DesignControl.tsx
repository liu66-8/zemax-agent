import { useDesignStore } from "@/stores/design";
import { invokeIPC } from "@/services/ipc";
import { Undo2, Redo2, Zap, Activity, Gauge } from "lucide-react";

export default function DesignControl() {
  const { surfaces, efl, fNumber, totalTrack, undo, redo } = useDesignStore();

  const quickActions = [
    { label: "光线追迹", icon: Zap, cmd: "system.get_system_info" },
    { label: "MTF 分析", icon: Activity, cmd: "analysis.get_mtf" },
    { label: "点列图", icon: Gauge, cmd: "analysis.get_spot" },
    { label: "光路布局", icon: Zap, cmd: "analysis.get_layout" },
  ];

  return (
    <div className="panel">
      <div className="flex-between mb-16">
        <h2>设计控制</h2>
        <div className="flex-between gap-8">
          <button className="btn btn-secondary" onClick={undo} title="撤销">
            <Undo2 size={14} /> 撤销
          </button>
          <button className="btn btn-secondary" onClick={redo} title="重做">
            <Redo2 size={14} /> 重做
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 20 }}>
        <InfoCard icon={Gauge} label="有效焦距" value={`${efl.toFixed(1)} mm`} />
        <InfoCard icon={Gauge} label="F 数" value={fNumber.toFixed(1)} />
        <InfoCard icon={Gauge} label="总长度" value={`${totalTrack.toFixed(1)} mm`} />
      </div>

      {surfaces.length === 0 ? (
        <div className="empty-state" style={{ padding: "32px 24px" }}>
          <Gauge size={40} />
          <p>暂无镜头数据<br />请先加载 ZMX 设计文件</p>
        </div>
      ) : (
        <div style={{ overflowX: "auto", marginBottom: 16 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th><th>面型</th><th>曲率半径 (mm)</th>
                <th>厚度 (mm)</th><th>玻璃</th><th>半口径 (mm)</th>
              </tr>
            </thead>
            <tbody>
              {surfaces.map((s) => (
                <tr key={s.index} className={s.is_stop ? "stop-row" : ""}>
                  <td>{s.index}{s.is_stop ? " ⏺" : ""}</td>
                  <td style={{ fontWeight: 500 }}>{s.surf_type}</td>
                  <td>{s.radius === 0 ? "∞" : s.radius.toFixed(3)}</td>
                  <td>{s.thickness.toFixed(3)}</td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: 11.5 }}>{s.glass || "—"}</td>
                  <td>{s.semi_diameter.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex-between gap-8" style={{ flexWrap: "wrap" }}>
        {quickActions.map((a) => (
          <button key={a.label} className="btn btn-secondary"
            onClick={() => invokeIPC(a.cmd, {}).catch(() => {})}>
            <a.icon size={14} /> {a.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function InfoCard({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="card" style={{ textAlign: "center", padding: "16px 12px" }}>
      <div style={{ color: "var(--text-tertiary)", fontSize: 11, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{value}</div>
    </div>
  );
}
