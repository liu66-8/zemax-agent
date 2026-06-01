import { create } from "zustand";

export interface SurfaceData {
  index: number; surf_type: string; radius: number;
  thickness: number; glass: string; semi_diameter: number;
  conic: number; is_stop: boolean;
}

interface DesignStore {
  surfaces: SurfaceData[];
  efl: number;
  fNumber: number;
  totalTrack: number;
  undoStack: SurfaceData[][];
  redoStack: SurfaceData[][];
  setLensData: (surfaces: SurfaceData[], efl: number, fNumber: number, totalTrack: number) => void;
  updateSurface: (index: number, field: string, value: string | number) => void;
  undo: () => void;
  redo: () => void;
}

export const useDesignStore = create<DesignStore>((set, get) => ({
  surfaces: [], efl: 0, fNumber: 0, totalTrack: 0, undoStack: [], redoStack: [],
  setLensData: (surfaces, efl, fNumber, totalTrack) =>
    set({ surfaces, efl, fNumber, totalTrack, undoStack: [], redoStack: [] }),
  updateSurface: (index, field, value) => {
    const prev = get().surfaces;
    set((s) => ({
      surfaces: s.surfaces.map((sf) => sf.index === index ? { ...sf, [field]: value } : sf),
      undoStack: [...s.undoStack, prev],
      redoStack: [],
    }));
  },
  undo: () => {
    const { undoStack, surfaces } = get();
    if (!undoStack.length) return;
    const prev = undoStack[undoStack.length - 1];
    set({ surfaces: prev, redoStack: [...get().redoStack, surfaces], undoStack: undoStack.slice(0, -1) });
  },
  redo: () => {
    const { redoStack, surfaces } = get();
    if (!redoStack.length) return;
    const next = redoStack[redoStack.length - 1];
    set({ surfaces: next, undoStack: [...get().undoStack, surfaces], redoStack: redoStack.slice(0, -1) });
  },
}));