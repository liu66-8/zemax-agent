"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

interface ModalCtx { open: (component: ReactNode) => void; close: () => void; }

const Ctx = createContext<ModalCtx>({ open: () => {}, close: () => {} });

export function ModalProvider({ children }: { children: ReactNode }) {
  const [modal, setModal] = useState<{ id: string; component: ReactNode } | null>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape" && modal) setModal(null); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [modal]);

  useEffect(() => {
    if (modal) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "";
    return () => { document.body.style.overflow = ""; };
  }, [modal]);

  return (
    <Ctx.Provider value={{
      open: (c) => setModal({ id: Math.random().toString(36), component: c }),
      close: () => setModal(null),
    }}>
      {children}
      {modal && (
        <div className="modal-overlay" onClick={() => setModal(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
            {modal.component}
          </div>
        </div>
      )}
    </Ctx.Provider>
  );
}

export function useModal() { return useContext(Ctx); }

export function ConfirmDialog({ title, message, onConfirm, onCancel, confirmLabel, cancelLabel }: {
  title: string; message: string; onConfirm: () => void;
  onCancel: () => void; confirmLabel?: string; cancelLabel?: string;
}) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Enter") onConfirm();
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onConfirm, onCancel]);

  return (
    <div>
      <h2>{title}</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: 13, lineHeight: 1.6 }}>{message}</p>
      <div className="modal-actions">
        <button className="btn btn-secondary" onClick={onCancel}>{cancelLabel || "取消"}</button>
        <button className="btn btn-primary" onClick={onConfirm}>{confirmLabel || "确认"}</button>
      </div>
    </div>
  );
}
