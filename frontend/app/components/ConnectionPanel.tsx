"use client";

import { useConnectionStore, useSettingsStore, type ConnStatus as ConnStatusType } from "@/app/stores";
import { Wifi, WifiOff, Settings, Loader2, Zap, Database } from "lucide-react";

export default function ConnectionPanel() {
  const { zos, qdrant, connectZOS, connectQdrant, disconnectZOS, disconnectQdrant } = useConnectionStore();
  const { setShowSettings } = useSettingsStore();

  return (
    <header className="topbar">
      <span className="topbar-title">仪表盘</span>
      <div className="topbar-status">
        <ConnBadge icon={Zap} name="OpticStudio" state={zos}
          onConnect={connectZOS} onDisconnect={disconnectZOS} />
        <ConnBadge icon={Database} name="Qdrant" state={qdrant}
          onConnect={connectQdrant} onDisconnect={disconnectQdrant} />
        <button className="btn btn-ghost btn-sm" onClick={() => setShowSettings(true)} title="系统设置">
          <Settings size={14} />
        </button>
      </div>
    </header>
  );
}

function ConnBadge({ icon: Icon, name, state, onConnect, onDisconnect }: {
  icon: any; name: string; state: { status: ConnStatusType; message: string; latencyMs: number };
  onConnect: () => void; onDisconnect: () => void;
}) {
  const isOn = state.status === "connected";
  const isConnecting = state.status === "connecting";
  const colors: Record<ConnStatusType, string> = {
    connected: "var(--success)", disconnected: "var(--error)", connecting: "var(--warning)", error: "var(--error)",
  };

  return (
    <span style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11.5, color: "var(--text-secondary)" }}>
      <div className={`status-dot ${isOn ? "on" : "off"}`}
        style={{ boxShadow: isConnecting ? "0 0 6px var(--warning)" : isOn ? "0 0 6px var(--success)" : undefined }} />
      <span>
        <Icon size={12} style={{ marginRight: 3, verticalAlign: -2 }} />
        {name} <span style={{ color: colors[state.status], fontSize: 10.5 }}>{state.message}</span>
        {isOn && <span style={{ color: "var(--text-tertiary)", marginLeft: 2 }}>· {state.latencyMs}ms</span>}
      </span>
      {isOn ? (
        <button className="btn btn-ghost btn-sm" onClick={onDisconnect} style={{ padding: "2px 6px", fontSize: 10 }}>断开</button>
      ) : isConnecting ? (
        <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} />
      ) : (
        <button className="btn btn-ghost btn-sm" onClick={onConnect} style={{ padding: "2px 6px", fontSize: 10 }}>连接</button>
      )}
    </span>
  );
}
