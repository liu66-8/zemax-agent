"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

interface ModalState { id: string; component: ReactNode; }

interface ModalCtx {
  open: (component: ReactNode) => void;
  close: () => void;
}

const Ctx = createContext<ModalCtx>({ open: () => {}, close: () => {} });

export function ModalProvider({ children }: { children: ReactNode }) {
  const [modal, setModal] = useState<ModalState | null>(null);

  return (
    <Ctx.Provider value={{
      open: (c) => setModal({ id: Math.random().toString(36), component: c }),
      close: () => setModal(null),
    }}>
      {children}
      {modal && (
        <div className="modal-overlay" onClick={() => setModal(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            {modal.component}
          </div>
        </div>
      )}
    </Ctx.Provider>
  );
}

export function useModal() { return useContext(Ctx); }

export function ConfirmDialog({ title, message, onConfirm, onCancel }: {
  title: string; message: string; onConfirm: () => void; onCancel: () => void;
}) {
  return (
    <div>
      <h2>{title}</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>{message}</p>
      <div className="modal-actions">
        <button className="btn btn-secondary" onClick={onCancel}>取消</button>
        <button className="btn btn-primary" onClick={onConfirm}>确认</button>
      </div>
    </div>
  );
}
