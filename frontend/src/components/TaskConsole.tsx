import { useTaskStore } from "@/stores";
import { Clock, CheckCircle2, XCircle, Loader2, AlertCircle } from "lucide-react";

const STATUS_MAP: Record<string, { label: string; color: string; soft: string; icon: any }> = {
  pending:   { label: "等待中", color: "var(--warning)",  soft: "var(--warning-soft)",  icon: Clock },
  running:   { label: "执行中", color: "var(--accent)",   soft: "var(--accent-soft)",   icon: Loader2 },
  completed: { label: "已完成", color: "var(--success)",  soft: "var(--success-soft)",  icon: CheckCircle2 },
  failed:    { label: "失败",   color: "var(--error)",    soft: "var(--error-soft)",    icon: XCircle },
  cancelled: { label: "已取消", color: "var(--text-tertiary)", soft: "transparent",     icon: AlertCircle },
};

export default function TaskConsole() {
  const { tasks, queueSize } = useTaskStore();

  return (
    <div className="panel">
      <div className="flex-between mb-16">
        <h2>任务控制台</h2>
        <span className="badge" style={{ background: "var(--bg-tertiary)", color: "var(--text-secondary)" }}>
          队列 {queueSize}
        </span>
      </div>

      {tasks.length === 0 ? (
        <div className="empty-state">
          <Clock size={44} />
          <p>暂无任务<br />执行设计操作时将在此显示任务进度</p>
        </div>
      ) : (
        tasks.map((t) => {
          const info = STATUS_MAP[t.status] || STATUS_MAP.pending;
          const Icon = info.icon;
          const isRunning = t.status === "running";
          return (
            <div key={t.id} className="card" style={{ marginBottom: 8 }}>
              <div className="flex-between" style={{ marginBottom: isRunning ? 10 : 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <Icon size={14} style={{ color: info.color }} />
                  <span style={{ fontWeight: 500, fontSize: 13.5 }}>{t.task_type}</span>
                </div>
                <span className="badge" style={{ background: info.soft, color: info.color }}>
                  {info.label}
                </span>
              </div>
              {isRunning && (
                <div>
                  <div style={{ height: 4, background: "var(--bg-primary)", borderRadius: 2, overflow: "hidden" }}>
                    <div style={{
                      height: "100%", width: `${Math.max(t.progress || 0, 5)}%`,
                      background: `linear-gradient(90deg, var(--accent), var(--success))`,
                      borderRadius: 2, transition: "width 0.4s ease-out",
                    }} />
                  </div>
                  <div style={{ fontSize: 10.5, color: "var(--text-tertiary)", marginTop: 5 }}>
                    {Math.round(t.progress || 0)}%
                  </div>
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
