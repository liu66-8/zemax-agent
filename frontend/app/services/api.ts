"use client";

import { useSettingsStore, useConnectionStore } from "@/app/stores";

const PYTHON_BASE = "http://127.0.0.1:9876";

type ApiOpts = {
  body?: any;
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

async function apiCall(endpoint: string, opts: ApiOpts = {}) {
  const { settings } = useSettingsStore.getState();
  const base = endpoint.startsWith("http") ? "" : endpoint.includes("/chat/completions") ? settings.llmApiBase : PYTHON_BASE;
  const url = endpoint.startsWith("http") ? endpoint : `${base}${endpoint}`;
  const isLLM = endpoint.includes("/chat/completions");

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(isLLM ? { Authorization: `Bearer ${settings.llmApiKey}` } : {}),
    ...opts.headers,
  };

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
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
  signal?: AbortSignal,
) {
  try {
    const res = await apiCall("/chat/completions", {
      body: {
        model: useSettingsStore.getState().settings.llmModel,
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
        } catch { /* skip */ }
      }
    }
    onDone();
  } catch (e: any) {
    if (e.name !== "AbortError") throw e;
  }
}

export function createTauriIPC() {
  async function checkHealth(target: string): Promise<{ connected: boolean; message: string; latencyMs: number }> {
    const start = performance.now();
    try {
      const res = await fetch(`${PYTHON_BASE}/api/health/${target}`);
      const data = await res.json();
      return { connected: data.connected, message: data.message, latencyMs: Math.round(performance.now() - start) };
    } catch {
      return { connected: false, message: "后端未启动", latencyMs: 0 };
    }
  }

  return {
    checkZOSConnection: () => checkHealth("zos"),
    checkQdrantConnection: () => checkHealth("qdrant"),

    async listProjects() {
      try {
        const res = await fetch(`${PYTHON_BASE}/api/projects`, { method: "POST" });
        return res.ok ? res.json() : [];
      } catch { return []; }
    },

    async createProject(name: string, description: string) {
      try {
        const res = await fetch(`${PYTHON_BASE}/api/projects`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, description }),
        });
        return res.ok ? res.json() : null;
      } catch { return null; }
    },

    async getLensData() {
      try {
        const res = await fetch(`${PYTHON_BASE}/api/lens`, { method: "POST" });
        return res.ok ? res.json() : null;
      } catch { return null; }
    },

    async getTasks() {
      try {
        const res = await fetch(`${PYTHON_BASE}/api/tasks`, { method: "POST" });
        return res.ok ? res.json() : [];
      } catch { return []; }
    },
  };
}
