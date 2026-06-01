"use client";

import { useSettingsStore, useConnectionStore } from "@/app/stores";

type ApiOpts = {
  body?: any;
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

async function apiCall(endpoint: string, opts: ApiOpts = {}) {
  const { settings } = useSettingsStore.getState();
  const base = settings.llmApiBase;
  const apiKey = settings.llmApiKey;

  const url = endpoint.startsWith("http") ? endpoint : `${base}${endpoint}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
      ...opts.headers,
    },
    body: JSON.stringify(opts.body),
    signal: opts.signal,
  });

  if (!res.ok) {
    const err = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${err}`);
  }
  return res;
}

export async function streamChat(
  messages: { role: string; content: string }[],
  onToken: (token: string) => void,
  onDone: () => void,
  signal?: AbortSignal
) {
  const { settings } = useSettingsStore.getState();

  try {
    const res = await apiCall("/chat/completions", {
      body: {
        model: settings.llmModel,
        messages,
        stream: true,
        temperature: 0.2,
        max_tokens: 4096,
      },
      signal,
    });

    const reader = res.body?.getReader();
    if (!reader) { onDone(); return; }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;
        const data = trimmed.slice(6);
        if (data === "[DONE]") { onDone(); return; }
        try {
          const parsed = JSON.parse(data);
          const token = parsed.choices?.[0]?.delta?.content;
          if (token) onToken(token);
        } catch { /* skip malformed */ }
      }
    }
    onDone();
  } catch (e: any) {
    if (e.name !== "AbortError") throw e;
  }
}

export function createTauriIPC() {
  return {
    async listProjects() {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        return await invoke("list_projects");
      } catch {
        const store = useConnectionStore.getState();
        const res = await fetch(`${store.python.status === "connected" ? "http://localhost:9876" : ""}/api/projects`);
        if (!res.ok) throw new Error("IPC not available");
        return res.json();
      }
    },

    async getProject(projectId: string) {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        return await invoke("get_project", { projectId });
      } catch { return null; }
    },

    async createProject(name: string, description: string) {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        return await invoke("create_project", { name, description });
      } catch { return null; }
    },

    async getLensData() {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        return await invoke("get_lens_data");
      } catch { return null; }
    },

    async runAnalysis(analysisType: string, params: Record<string, unknown> = {}) {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        return await invoke(`run_${analysisType}`, params);
      } catch { return null; }
    },

    async getTasks() {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        return await invoke("get_tasks");
      } catch { return []; }
    },

    async checkZOSConnection(): Promise<boolean> {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        const result = await invoke("check_zos_connection");
        return !!result;
      } catch {
        try {
          const res = await fetch("http://localhost:9876/api/health/zos");
          return res.ok;
        } catch { return false; }
      }
    },

    async checkQdrantConnection(): Promise<boolean> {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        const result = await invoke("check_qdrant_connection");
        return !!result;
      } catch {
        try {
          const res = await fetch("http://localhost:9876/api/health/qdrant");
          return res.ok;
        } catch { return false; }
      }
    },
  };
}
