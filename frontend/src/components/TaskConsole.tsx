import { useTaskStore } from "@/stores";

const STATUS_CN: Record<string, string> = {
  pending: "等待中", running: "执行中", completed: "已完成", failed: "失败", cancelled: "已取消",
};

export default function TaskConsole() {
  const { tasks, queueSize } = useTaskStore();

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ fontSize: 16, margin: 0 }}>任务控制台</h2>
        <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>队列: {queueSize}</span>
      </div>

      {tasks.length === 0 ? (
        <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>暂无任务。执行设计操作时将在此显示任务进度。</p>
      ) : (
        <div>
          {tasks.map((t) => (
            <div key={t.id} style={{
              padding: "10px 12px", background: "var(--bg-tertiary)", borderRadius: 6, marginBottom: 6,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{t.task_type}</span>
                <StatusBadge status={t.status} />
              </div>
              {t.status === "running" && (
                <div style={{ marginTop: 6 }}>
                  <div style={{ height: 3, background: "var(--bg-primary)", borderRadius: 2 }}>
                    <div style={{
                      height: "100%", width: `${t.progress}%`,
                      background: "var(--accent)", borderRadius: 2, transition: "width 0.3s",
                    }} />
                  </div>
                  <div style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 3 }}>{t.progress}%</div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = { pending: "#eab308", running: "#3b82f6", completed: "#22c55e", failed: "#ef4444", cancelled: "#94a3b8" };
  return (
    <span style={{
      padding: "2px 8px", borderRadius: 10, fontSize: 10, fontWeight: 500,
      background: (colors[status] || "#64748b") + "20",
      color: colors[status] || "#64748b",
    }}>
      {STATUS_CN[status] || status}
    </span>
  );
}
