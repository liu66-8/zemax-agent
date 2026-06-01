"use client";

import { ListChecks, CheckCircle2, Clock, XCircle, Loader2 } from "lucide-react";
import { useTaskStore } from "@/app/stores";

const statusIcons: Record<string, any> = { pending: Clock, running: Loader2, completed: CheckCircle2, failed: XCircle };
const statusColors: Record<string, string> = { pending: "var(--warning)", running: "var(--accent)", completed: "var(--success)", failed: "var(--error)" };
const statusLabels: Record<string, string> = { pending: "等待", running: "执行", completed: "完成", failed: "失败" };

export default function TaskPanel() {
  const { tasks } = useTaskStore();

  return (
    <div className="panel-box">
      <div className="panel-hdr">
        <ListChecks size={14} style={{ color: "var(--warning)" }} />
        <h3>任务</h3>
      </div>
      <div className="panel-body">
        {tasks.length === 0 ? (
          <div style={{ textAlign: "center", padding: "32px 0", color: "var(--text-tertiary)", fontSize: 12 }}>
            <ListChecks size={28} style={{ opacity: 0.15, marginBottom: 6 }} />
            <p>暂无任务</p>
          </div>
        ) : (
          tasks.map((t) => {
            const Icon = statusIcons[t.status] || Clock;
            return (
              <div key={t.id} style={{ padding: "8px 0", borderBottom: "1px solid var(--border-light)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Icon size={13} style={{ color: statusColors[t.status] || "var(--text-tertiary)" }} />
                  <span style={{ fontSize: 12.5 }}>{t.task_type}</span>
                </div>
                <span style={{ fontSize: 11, color: statusColors[t.status] || "var(--text-tertiary)" }}>
                  {t.status === "running" ? `${Math.round(t.progress)}%` : statusLabels[t.status] || t.status}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
