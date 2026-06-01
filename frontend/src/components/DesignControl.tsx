import { useDesignStore } from "@/stores/design";
import { invokeIPC } from "@/services/ipc";

export default function DesignControl() {
  const { surfaces, efl, fNumber, totalTrack, updateSurface, undo, redo } = useDesignStore();

  const quickActions = [
    { label: "光线追迹", cmd: "system.get_system_info" },
    { label: "MTF 分析", cmd: "analysis.get_mtf" },
    { label: "点列图", cmd: "analysis.get_spot" },
    { label: "光路布局", cmd: "analysis.get_layout" },
  ];

  const runAction = async (cmd: string) => {
    try { await invokeIPC(cmd, {}); } catch { /* mock */ }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ fontSize: 16, margin: 0 }}>设计控制</h2>
        <div style={{ display: "flex", gap: 4 }}>
          <button onClick={undo} style={smallBtn} title="撤销">↩</button>
          <button onClick={redo} style={smallBtn} title="重做">↪</button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 16 }}>
        <InfoCard label="有效焦距" value={`${efl.toFixed(1)} mm`} />
        <InfoCard label="F 数" value={fNumber.toFixed(1)} />
        <InfoCard label="总长度" value={`${totalTrack.toFixed(1)} mm`} />
      </div>

      {surfaces.length === 0 ? (
        <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>暂无镜头数据，请先加载设计文件。</p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["#", "面型", "曲率半径", "厚度", "玻璃", "半口径"].map((h) => (
                  <th key={h} style={thStyle}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {surfaces.map((s) => (
                <tr key={s.index} style={{ background: s.is_stop ? "rgba(59,130,246,0.1)" : "transparent" }}>
                  <td style={tdStyle}>{s.index}{s.is_stop ? " ⏺" : ""}</td>
                  <td style={tdStyle}>{s.surf_type}</td>
                  <td style={tdStyle}>{s.radius.toFixed(2)}</td>
                  <td style={tdStyle}>{s.thickness.toFixed(2)}</td>
                  <td style={tdStyle}>{s.glass}</td>
                  <td style={tdStyle}>{s.semi_diameter.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        {quickActions.map((a) => (
          <button key={a.label} onClick={() => runAction(a.cmd)}
            style={{ padding: "6px 14px", background: "var(--bg-tertiary)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-primary)", fontSize: 12, cursor: "pointer" }}>
            {a.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ padding: "10px 12px", background: "var(--bg-tertiary)", borderRadius: 6, textAlign: "center" }}>
      <div style={{ fontSize: 10, color: "var(--text-secondary)" }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 600, marginTop: 2 }}>{value}</div>
    </div>
  );
}

const thStyle: React.CSSProperties = { padding: "6px 10px", textAlign: "left", fontSize: 11, color: "var(--text-secondary)", borderBottom: "1px solid var(--border)" };
const tdStyle: React.CSSProperties = { padding: "5px 10px", fontSize: 12, borderBottom: "1px solid var(--border)" };
const smallBtn: React.CSSProperties = { padding: "4px 8px", background: "var(--bg-tertiary)", border: "1px solid var(--border)", borderRadius: 4, color: "var(--text-primary)", cursor: "pointer" };
