"use client";
import { create } from "zustand";

export interface ProjectItem {
  id: string; name: string; description: string;
  system_type: string; design_phase: string; tags: string[]; created_at: string;
}

interface ProjectStore {
  projects: ProjectItem[]; current: ProjectItem | null; loading: boolean;
  setProjects: (p: ProjectItem[]) => void; setCurrent: (p: ProjectItem | null) => void;
  setLoading: (v: boolean) => void;
}
export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [], current: null, loading: false,
  setProjects: (p) => set({ projects: p }),
  setCurrent: (p) => set({ current: p }),
  setLoading: (v) => set({ loading: v }),
}));

export type ConnStatus = "connected" | "disconnected" | "connecting" | "error";

interface ConnState { status: ConnStatus; message: string; latencyMs: number; }
interface ConnectionStore {
  zos: ConnState; qdrant: ConnState; python: ConnState;
  setZOS: (s: Partial<ConnState>) => void; setQdrant: (s: Partial<ConnState>) => void;
  setPython: (s: Partial<ConnState>) => void;
  connectZOS: () => Promise<void>; connectQdrant: () => Promise<void>;
  disconnectZOS: () => void; disconnectQdrant: () => void;
}
export const useConnectionStore = create<ConnectionStore>((set) => ({
  zos: { status: "disconnected", message: "未连接", latencyMs: 0 },
  qdrant: { status: "disconnected", message: "未连接", latencyMs: 0 },
  python: { status: "disconnected", message: "未启动", latencyMs: 0 },
  setZOS: (s) => set((st) => ({ zos: { ...st.zos, ...s } })),
  setQdrant: (s) => set((st) => ({ qdrant: { ...st.qdrant, ...s } })),
  setPython: (s) => set((st) => ({ python: { ...st.python, ...s } })),
  connectZOS: async () => {
    set((st) => ({ zos: { ...st.zos, status: "connecting", message: "连接中..." } }));
    const start = performance.now();
    try {
      const { createTauriIPC } = await import("@/app/services/api");
      const ipc = createTauriIPC();
      const ok = await ipc.checkZOSConnection();
      const latency = Math.round(performance.now() - start);
      set((st) => ({ zos: { ...st.zos, status: ok ? "connected" : "error", message: ok ? "已连接" : "连接失败", latencyMs: ok ? latency : 0 } }));
    } catch {
      set((st) => ({ zos: { ...st.zos, status: "error", message: "连接失败", latencyMs: 0 } }));
    }
  },
  connectQdrant: async () => {
    set((st) => ({ qdrant: { ...st.qdrant, status: "connecting", message: "连接中..." } }));
    const start = performance.now();
    try {
      const { createTauriIPC } = await import("@/app/services/api");
      const ipc = createTauriIPC();
      const ok = await ipc.checkQdrantConnection();
      const latency = Math.round(performance.now() - start);
      set((st) => ({ qdrant: { ...st.qdrant, status: ok ? "connected" : "error", message: ok ? "已连接" : "连接失败", latencyMs: ok ? latency : 0 } }));
    } catch {
      set((st) => ({ qdrant: { ...st.qdrant, status: "error", message: "连接失败", latencyMs: 0 } }));
    }
  },
  disconnectZOS: () => set((st) => ({ zos: { ...st.zos, status: "disconnected", message: "已断开", latencyMs: 0 } })),
  disconnectQdrant: () => set((st) => ({ qdrant: { ...st.qdrant, status: "disconnected", message: "已断开", latencyMs: 0 } })),
}));

export interface FileEntry { name: string; path: string; size: number; type: "zmx" | "analysis" | "report" | "other"; modified: string; }
export interface RecentFile { name: string; path: string; openedAt: string; }
interface FileStore {
  currentFile: string | null; recentFiles: RecentFile[]; workspaceFiles: FileEntry[];
  setCurrentFile: (path: string | null) => void; addRecent: (f: RecentFile) => void;
  setWorkspaceFiles: (files: FileEntry[]) => void;
}
export const useFileStore = create<FileStore>((set) => ({
  currentFile: null, recentFiles: [], workspaceFiles: [],
  setCurrentFile: (p) => set({ currentFile: p }),
  addRecent: (f) => set((s) => ({ recentFiles: [f, ...s.recentFiles.filter((r) => r.path !== f.path)].slice(0, 8) })),
  setWorkspaceFiles: (files) => set({ workspaceFiles: files }),
}));

export interface AppSettings {
  zosMode: "standalone" | "extension"; zosTimeout: number;
  qdrantUrl: string;
  llmProvider: string; llmModel: string; llmApiBase: string; llmApiKey: string;
  theme: "dark" | "light";
}
interface SettingsStore {
  settings: AppSettings; showSettings: boolean;
  update: (s: Partial<AppSettings>) => void; setShowSettings: (v: boolean) => void;
}
export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: {
    zosMode: "standalone", zosTimeout: 30,
    qdrantUrl: "http://localhost:6333",
    llmProvider: "deepseek", llmModel: "deepseek-chat",
    llmApiBase: "https://api.deepseek.com/v1",
    llmApiKey: "",
    theme: "dark",
  },
  showSettings: false,
  update: (s) => set((st) => ({ settings: { ...st.settings, ...s } })),
  setShowSettings: (v) => set({ showSettings: v }),
}));

interface Message { role: string; content: string; }
interface ChatStore { messages: Message[]; isStreaming: boolean; addMessage: (m: Message) => void; setStreaming: (s: boolean) => void; clear: () => void; }
export const useChatStore = create<ChatStore>((set) => ({
  messages: [], isStreaming: false,
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  setStreaming: (s) => set({ isStreaming: s }),
  clear: () => set({ messages: [] }),
}));

export interface SurfaceData { index: number; surf_type: string; radius: number; thickness: number; glass: string; semi_diameter: number; conic: number; is_stop: boolean; }
interface DesignStore {
  surfaces: SurfaceData[]; efl: number; fNumber: number; totalTrack: number; loading: boolean;
  undoStack: SurfaceData[][]; redoStack: SurfaceData[][];
  setLensData: (s: SurfaceData[], e: number, f: number, t: number) => void; setLoading: (v: boolean) => void;
  updateSurface: (idx: number, field: string, val: string | number) => void;
  undo: () => void; redo: () => void;
}
export const useDesignStore = create<DesignStore>((set, get) => ({
  surfaces: [], efl: 0, fNumber: 0, totalTrack: 0, loading: false, undoStack: [], redoStack: [],
  setLensData: (s, e, f, t) => set({ surfaces: s, efl: e, fNumber: f, totalTrack: t, undoStack: [], redoStack: [], loading: false }),
  setLoading: (v) => set({ loading: v }),
  updateSurface: (idx, field, val) => {
    const prev = get().surfaces;
    set((s) => ({ surfaces: s.surfaces.map((sf) => sf.index === idx ? { ...sf, [field]: val } : sf), undoStack: [...s.undoStack, prev], redoStack: [] }));
  },
  undo: () => { const { undoStack, surfaces } = get(); if (!undoStack.length) return; set({ surfaces: undoStack[undoStack.length - 1], redoStack: [...get().redoStack, surfaces], undoStack: undoStack.slice(0, -1) }); },
  redo: () => { const { redoStack, surfaces } = get(); if (!redoStack.length) return; set({ surfaces: redoStack[redoStack.length - 1], undoStack: [...get().undoStack, surfaces], redoStack: redoStack.slice(0, -1) }); },
}));

interface TaskItem { id: string; task_type: string; status: string; progress: number; created_at: string; }
interface TaskStore { tasks: TaskItem[]; queueSize: number; setTasks: (t: TaskItem[]) => void; setQueueSize: (s: number) => void; }
export const useTaskStore = create<TaskStore>((set) => ({ tasks: [], queueSize: 0, setTasks: (t) => set({ tasks: t }), setQueueSize: (s) => set({ queueSize: s }) }));
