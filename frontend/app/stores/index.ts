"use client";
import { create } from "zustand";

export interface ProjectItem {
  id: string; name: string; description: string;
  system_type: string; design_phase: string; tags: string[]; created_at: string;
}

interface ProjectStore {
  projects: ProjectItem[];
  current: ProjectItem | null;
  setProjects: (p: ProjectItem[]) => void;
  setCurrent: (p: ProjectItem | null) => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [], current: null,
  setProjects: (p) => set({ projects: p }),
  setCurrent: (p) => set({ current: p }),
}));

interface Message { role: string; content: string; }

interface ChatStore {
  messages: Message[]; isStreaming: boolean;
  addMessage: (m: Message) => void;
  setStreaming: (s: boolean) => void;
  clear: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [], isStreaming: false,
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  setStreaming: (s) => set({ isStreaming: s }),
  clear: () => set({ messages: [] }),
}));

export interface SurfaceData {
  index: number; surf_type: string; radius: number;
  thickness: number; glass: string; semi_diameter: number;
  conic: number; is_stop: boolean;
}

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
    set((s) => ({
      surfaces: s.surfaces.map((sf) => sf.index === idx ? { ...sf, [field]: val } : sf),
      undoStack: [...s.undoStack, prev], redoStack: [],
    }));
  },
  undo: () => {
    const { undoStack, surfaces } = get();
    if (!undoStack.length) return;
    set({ surfaces: undoStack[undoStack.length - 1], redoStack: [...get().redoStack, surfaces], undoStack: undoStack.slice(0, -1) });
  },
  redo: () => {
    const { redoStack, surfaces } = get();
    if (!redoStack.length) return;
    set({ surfaces: redoStack[redoStack.length - 1], undoStack: [...get().undoStack, surfaces], redoStack: redoStack.slice(0, -1) });
  },
}));

interface TaskItem { id: string; task_type: string; status: string; progress: number; }

interface TaskStore {
  tasks: TaskItem[]; queueSize: number;
  setTasks: (t: TaskItem[]) => void;
  setQueueSize: (s: number) => void;
}

export const useTaskStore = create<TaskStore>((set) => ({
  tasks: [], queueSize: 0,
  setTasks: (t) => set({ tasks: t }),
  setQueueSize: (s) => set({ queueSize: s }),
}));

export type PanelKey = "design" | "analysis" | "ai" | "tasks" | "versions" | "knowledge";

interface UIStore {
  panelLayout: PanelKey[][];
  setLayout: (layout: PanelKey[][]) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  panelLayout: [["design", "analysis"], ["ai", "tasks"]],
  setLayout: (l) => set({ panelLayout: l }),
}));
