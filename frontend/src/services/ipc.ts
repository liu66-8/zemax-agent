export interface ProjectMeta {
  id: string;
  name: string;
  description: string;
  system_type: string;
  design_phase: string;
  tags: string[];
  created_at: string;
}

export interface IPCMessage {
  type: string;
  id?: string;
  command?: string;
  params?: Record<string, unknown>;
  data?: unknown;
  error?: string;
  progress?: number;
  message?: string;
}

let _ipcCallback: ((msg: IPCMessage) => void) | null = null;

export function onIPCMessage(callback: (msg: IPCMessage) => void) {
  _ipcCallback = callback;
}

export function sendIPC(msg: IPCMessage): void {
  try {
    console.log("[IPC]", JSON.stringify(msg));
  } catch { /* ignore */ }
}

export async function invokeIPC(command: string, params: Record<string, unknown> = {}): Promise<unknown> {
  try {
    if (window.__TAURI_INTERNALS__) {
      const { invoke } = await import("@tauri-apps/api/core");
      return await invoke(command, params);
    }
  } catch { /* ignore */ }
  console.log(`[IPC invoke] ${command}`, params);
  return null;
}
