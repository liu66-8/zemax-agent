import { create } from "zustand";
import type { ProjectMeta } from "@/services/ipc";

interface ProjectStore {
  projects: ProjectMeta[];
  currentProject: ProjectMeta | null;
  setProjects: (projects: ProjectMeta[]) => void;
  setCurrent: (project: ProjectMeta | null) => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  currentProject: null,
  setProjects: (projects) => set({ projects }),
  setCurrent: (project) => set({ currentProject: project }),
}));

interface Message { role: string; content: string; }

interface ChatStore {
  messages: Message[];
  isStreaming: boolean;
  addMessage: (msg: Message) => void;
  setStreaming: (streaming: boolean) => void;
  clear: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isStreaming: false,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  clear: () => set({ messages: [] }),
}));

interface TaskItem {
  id: string; task_type: string; status: string;
  progress: number; created_at: string;
}

interface TaskStore {
  tasks: TaskItem[];
  queueSize: number;
  setTasks: (tasks: TaskItem[]) => void;
  setQueueSize: (size: number) => void;
}

export const useTaskStore = create<TaskStore>((set) => ({
  tasks: [],
  queueSize: 0,
  setTasks: (tasks) => set({ tasks }),
  setQueueSize: (size) => set({ queueSize: size }),
}));

interface Notification {
  id: string; type: "info" | "warning" | "error";
  message: string; timestamp: number;
}

interface UIStore {
  theme: "dark" | "light";
  notifications: Notification[];
  setTheme: (theme: "dark" | "light") => void;
  addNotification: (n: Omit<Notification, "id" | "timestamp">) => void;
  removeNotification: (id: string) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  theme: "dark",
  notifications: [],
  setTheme: (theme) => set({ theme }),
  addNotification: (n) =>
    set((s) => ({
      notifications: [
        ...s.notifications,
        { ...n, id: `${Date.now()}`, timestamp: Date.now() },
      ],
    })),
  removeNotification: (id) =>
    set((s) => ({
      notifications: s.notifications.filter((n) => n.id !== id),
    })),
}));
