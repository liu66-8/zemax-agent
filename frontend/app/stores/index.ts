"use client";
import { create } from "zustand";

export interface ProjectItem {
  id: string; name: string; description: string;
  system_type: string; design_phase: string; tags: string[]; created_at: string;
}

interface ProjectStore {
  projects: ProjectItem[]; current: ProjectItem | null;
  setProjects: (p: ProjectItem[]) => void; setCurrent: (p: ProjectItem | null) => void;
}
export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [], current: null,
  setProjects: (p) => set({ projects: p }),
  setCurrent: (p) => set({ current: p }),
}));

// ── Connection Store ──
export type ConnStatus = "connected" | "disconnected" | "connecting" | "error";

interface ConnState { status: ConnStatus; message: string; latencyMs: number; }
interface ConnectionStore {
  zos: ConnState; qdrant: ConnState; python: ConnState;
  setZOS: (s: Partial<ConnState>) => void;
  setQdrant: (s: Partial<ConnState>) => void;
  setPython: (s: Partial<ConnState>) => void;
  connect: (target: "zos" | "qdrant") => void;
  disconnect: (target: "zos" | "qdrant") => void;
}
export const useConnectionStore = create<ConnectionStore>((set) => ({
  zos: { status: "disconnected", message: "未连接", latencyMs: 0 },
  qdrant: { status: "disconnected", message: "未连接", latencyMs: 0 },
  python: { status: "disconnected", message: "未启动", latencyMs: 0 },
  setZOS: (s) => set((st) => ({ zos: { ...st.zos, ...s } })),
  setQdrant: (s) => set((st) => ({ qdrant: { ...st.qdrant, ...s } })),
  setPython: (s) => set((st) => ({ python: { ...st.python, ...s } })),
  connect: (t) => {
    const setter = t === "zos" ? "setZOS" : "setQdrant";
    set((st) => {
      const current = t === "zos" ? st.zos : st.qdrant;
      return { [t]: { ...current, status: "connecting", message: "连接中..." } } as any;
    });
    setTimeout(() => {
      set((st) => {
        const current = t === "zos" ? st.zos : st.qdrant;
        return { [t]: { ...current, status: "connected", message: "已连接", latencyMs: 45 } } as any;
      });
    }, 1500);
  },
  disconnect: (t) => {
    set((st) => {
      const current = t === "zos" ? st.zos : st.qdrant;
      return { [t]: { ...current, status: "disconnected", message: "未连接", latencyMs: 0 } } as any;
    });
  },
}));

// ── File Store ──
export interface FileEntry { name: string; path: string; size: number; type: "zmx" | "analysis" | "report" | "other"; modified: string; }
export interface RecentFile { name: string; path: string; openedAt: string; }
interface FileStore {
  currentFile: string | null;
  recentFiles: RecentFile[];
  workspaceFiles: FileEntry[];
  setCurrentFile: (path: string | null) => void;
  addRecent: (f: RecentFile) => void;
  setWorkspaceFiles: (files: FileEntry[]) => void;
}
export const useFileStore = create<FileStore>((set) => ({
  currentFile: null,
  recentFiles: [],
  workspaceFiles: [],
  setCurrentFile: (p) => set({ currentFile: p }),
  addRecent: (f) => set((s) => {
    const filtered = s.recentFiles.filter((r) => r.path !== f.path);
    return { recentFiles: [f, ...filtered].slice(0, 8) };
  }),
  setWorkspaceFiles: (files) => set({ workspaceFiles: files }),
}));

// ── Settings Store ──
export interface AppSettings {
  zosMode: "standalone" | "extension";
  zosTimeout: number;
  qdrantUrl: string;
  llmProvider: string; llmModel: string; llmApiBase: string;
  theme: "dark" | "light";
}
interface SettingsStore {
  settings: AppSettings; showSettings: boolean;
  update: (s: Partial<AppSettings>) => void;
  setShowSettings: (v: boolean) => void;
}
export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: { zosMode: "standalone", zosTimeout: 30, qdrantUrl: "http://localhost:6333", llmProvider: "openai", llmModel: "gpt-4", llmApiBase: "https://api.openai.com/v1", theme: "dark" },
  showSettings: false,
  update: (s) => set((st) => ({ settings: { ...st.settings, ...s } })),
  setShowSettings: (v) => set({ showSettings: v }),
}));

// ── Chat Store ──
interface Message { role: string; content: string; }
interface ChatStore { messages: Message[]; isStreaming: boolean; addMessage: (m: Message) => void; setStreaming: (s: boolean) => void; clear: () => void; }
export const useChatStore = create<ChatStore>((set) => ({
  messages: [], isStreaming: false,
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  setStreaming: (s) => set({ isStreaming: s }),
  clear: () => set({ messages: [] }),
}));

// ── Design Store ──
export interface SurfaceData { index: number; surf_type: string; radius: number; thickness: number; glass: string; semi_diameter: number; conic: number; is_stop: boolean; }
interface DesignStore {
  surfaces: SurfaceData[]; efl: number; fNumber: number; totalTrack: number;
  undoStack: SurfaceData[][]; redoStack: SurfaceData[][];
  setLensData: (s: SurfaceData[], e: number, f: number, t: number) => void;
  updateSurface: (idx: number, field: string, val: string | number) => void;
  undo: () => void; redo: () => void;
}
export const useDesignStore = create<DesignStore>((set, get) => ({
  surfaces: [], efl: 0, fNumber: 0, totalTrack: 0, undoStack: [], redoStack: [],
  setLensData: (s, e, f, t) => set({ surfaces: s, efl: e, fNumber: f, totalTrack: t, undoStack: [], redoStack: [] }),
  updateSurface: (idx, field, val) => {
    const prev = get().surfaces;
    set((s) => ({ surfaces: s.surfaces.map((sf) => sf.index === idx ? { ...sf, [field]: val } : sf), undoStack: [...s.undoStack, prev], redoStack: [] }));
  },
  undo: () => { const { undoStack, surfaces } = get(); if (!undoStack.length) return; set({ surfaces: undoStack[undoStack.length - 1], redoStack: [...get().redoStack, surfaces], undoStack: undoStack.slice(0, -1) }); },
  redo: () => { const { redoStack, surfaces } = get(); if (!redoStack.length) return; set({ surfaces: redoStack[redoStack.length - 1], undoStack: [...get().undoStack, surfaces], redoStack: redoStack.slice(0, -1) }); },
}));

// ── Task Store ──
interface TaskItem { id: string; task_type: string; status: string; progress: number; }
interface TaskStore { tasks: TaskItem[]; queueSize: number; setTasks: (t: TaskItem[]) => void; setQueueSize: (s: number) => void; }
export const useTaskStore = create<TaskStore>((set) => ({ tasks: [], queueSize: 0, setTasks: (t) => set({ tasks: t }), setQueueSize: (s) => set({ queueSize: s }) }));
