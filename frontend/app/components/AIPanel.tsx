"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { Send, Sparkles, StopCircle, Wrench } from "lucide-react";
import { useChatStore, useSettingsStore, useProjectStore, useDesignStore, useTaskStore } from "@/app/stores";

const PYTHON_BASE = "http://127.0.0.1:9876";

export default function AIPanel() {
  const { messages, isStreaming, addMessage, setStreaming } = useChatStore();
  const { settings } = useSettingsStore();
  const { current: project } = useProjectStore();
  const { setLensData } = useDesignStore();
  const { setTasks } = useTaskStore();
  const [input, setInput] = useState("");
  const [buf, setBuf] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [tools, setTools] = useState<any[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const initRef = useRef(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, buf]);

  useEffect(() => {
    if (!initRef.current && !messages.length) {
      initRef.current = true;
      addMessage({ role: "system", content: "👋 描述您的光学设计任务即可开始" });
    }
  }, []);

  useEffect(() => {
    fetch(`${PYTHON_BASE}/api/zos/tools`).then((r) => r.json()).then(setTools).catch(() => {});
  }, []);

  function syncLensData(surfaces: any[], efl: number, fNumber: number, totalTrack: number) {
    setLensData(
      surfaces.map((s: any, i: number) => ({
        index: s.index || i + 1, surf_type: s.surf_type || "Standard",
        radius: s.radius || 0, thickness: s.thickness || 0,
        glass: s.glass || "", semi_diameter: s.semi_diameter || 10,
        conic: s.conic || 0, is_stop: s.is_stop || false,
      })),
      efl, fNumber, totalTrack,
    );
  }

  async function executeTool(toolName: string, params: Record<string, unknown>) {
    const res = await fetch(`${PYTHON_BASE}/api/zos/execute`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tool: toolName, params }),
    });
    if (!res.ok) throw new Error(`Tool ${toolName} failed: ${res.status}`);
    return res.json();
  }

  const send = useCallback(async () => {
    if (!input.trim() || isStreaming) return;
    if (!settings.llmApiKey) { setError("请先在设置中配置 API Key"); return; }
    setError(null);
    const userMsg = input.trim();
    addMessage({ role: "user", content: userMsg });
    setInput("");
    setStreaming(true);
    setBuf("");

    const controller = new AbortController();
    abortRef.current = controller;

    const chatMessages = [
      { role: "system", content: `你是 Zemax Agent 的光学工程 AI 助手。当前项目: ${project?.name || "无"}。你可以调用 Zemax 工具来创建设计、运行分析和执行优化。当用户要求设计镜头时，主动使用工具。用中文回复。` },
      ...messages.filter((m) => m.role !== "system" && m.content).slice(-10).map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
      { role: "user", content: userMsg },
    ];

    try {
      const body: any = { model: settings.llmModel, messages: chatMessages, temperature: 0.2, max_tokens: 4096 };
      if (tools.length > 0) body.tools = tools;

      const llmRes = await fetch(`${settings.llmApiBase}/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${settings.llmApiKey}` },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!llmRes.ok) { const errText = await llmRes.text(); throw new Error(`LLM error ${llmRes.status}: ${errText.slice(0, 100)}`); }

      const llmData = await llmRes.json();
      const choice = llmData.choices?.[0];
      const toolCalls = choice?.message?.tool_calls;

      if (toolCalls && toolCalls.length > 0) {
        // Execute tools and feed results back to LLM
        const toolResults: { role: string; tool_call_id: string; content: string }[] = [];
        const toolMessages: string[] = [];

        for (const tc of toolCalls) {
          const toolName = tc.function.name;
          const args = JSON.parse(tc.function.arguments || "{}");
          toolMessages.push(`🔧 调用 ${toolName}(${JSON.stringify(args)})...`);

          try {
            const result = await executeTool(toolName, args);
            const resultStr = JSON.stringify(result.data || result);
            toolResults.push({ role: "tool", tool_call_id: tc.id, content: resultStr });
            toolMessages.push(`✅ ${toolName} 完成`);

            // Sync to design panel
            if (toolName === "zos_get_lens_summary" || toolName === "zos_create_cooke_triplet" || toolName === "zos_load_zmx" || toolName === "zos_create_doublet") {
              const d = result.data;
              if (d?.surfaces) syncLensData(d.surfaces, d.effective_focal_length || 100, d.f_number || 4, d.total_track || 100);
            }

            const taskLabel = toolName.replace("zos_", "");
            setTasks([{
              id: Date.now().toString(), task_type: taskLabel, status: "completed", progress: 100,
              created_at: new Date().toISOString(),
            }]);
          } catch (e: any) {
            toolMessages.push(`❌ ${toolName} 失败: ${e.message}`);
            toolResults.push({ role: "tool", tool_call_id: tc.id, content: `Error: ${e.message}` });
          }
        }

        addMessage({ role: "assistant", content: toolMessages.join("\n") });

        // Send results back to LLM for final response
        const followUpMessages = [
          ...chatMessages,
          { role: "assistant" as const, content: "", tool_calls: toolCalls },
          ...toolResults,
          { role: "user", content: "请基于以上工具执行结果，总结设计状态并给出下一步建议。用中文回复。" },
        ];

        const finalRes = await fetch(`${settings.llmApiBase}/chat/completions`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${settings.llmApiKey}` },
          body: JSON.stringify({ model: settings.llmModel, messages: followUpMessages.slice(-20), temperature: 0.2, max_tokens: 2048, stream: true }),
          signal: controller.signal,
        });

        const reader = finalRes.body?.getReader();
        if (reader) {
          const decoder = new TextDecoder();
          let buf2 = "", full = "";
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf2 += decoder.decode(value, { stream: true });
            const lines = buf2.split("\n"); buf2 = lines.pop() || "";
            for (const line of lines) {
              const t = line.trim(); if (!t.startsWith("data: ")) continue;
              const d = t.slice(6); if (d === "[DONE]") break;
              try { const p = JSON.parse(d); const tok = p.choices?.[0]?.delta?.content; if (tok) { full += tok; setBuf(full); } } catch {}
            }
          }
          if (full) addMessage({ role: "assistant", content: full });
        }
        setBuf(""); setStreaming(false);
      } else if (choice?.message?.content) {
        addMessage({ role: "assistant", content: choice.message.content });
        setStreaming(false);
      } else {
        // Fallback: stream response
        const streamRes = await fetch(`${settings.llmApiBase}/chat/completions`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${settings.llmApiKey}` },
          body: JSON.stringify({ model: settings.llmModel, messages: chatMessages, temperature: 0.2, max_tokens: 4096, stream: true }),
          signal: controller.signal,
        });
        const reader = streamRes.body?.getReader();
        if (reader) {
          const decoder = new TextDecoder();
          let b = "", full = "";
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            b += decoder.decode(value, { stream: true });
            const lines = b.split("\n"); b = lines.pop() || "";
            for (const line of lines) {
              const t = line.trim(); if (!t.startsWith("data: ")) continue;
              const d = t.slice(6); if (d === "[DONE]") break;
              try { const p = JSON.parse(d); const tok = p.choices?.[0]?.delta?.content; if (tok) { full += tok; setBuf(full); } } catch {}
            }
          }
          if (full) addMessage({ role: "assistant", content: full });
        }
        setBuf(""); setStreaming(false);
      }
    } catch (e: unknown) {
      if ((e as Error).name !== "AbortError") setError((e as Error).message || "请求失败");
      setBuf(""); setStreaming(false);
    }
  }, [input, isStreaming, messages, project, settings, tools, addMessage, setStreaming, setLensData, setTasks]);

  const stop = () => { abortRef.current?.abort(); setStreaming(false); setBuf(""); };

  const shortcuts = [
    { label: "创建 Triplet", cmd: "创建一个焦距100mm、F/4的Cooke三片式镜头" },
    { label: "MTF 分析", cmd: "运行MTF分析并报告结果" },
    { label: "优化设计", cmd: "对当前设计执行优化" },
    { label: "像差诊断", cmd: "分析像差并给出校正建议" },
  ];

  return (
    <div className="panel-box">
      <div className="panel-hdr">
        <Sparkles size={14} style={{ color: "var(--purple)" }} />
        <h3>AI 助手</h3>
        <span style={{ marginLeft: 8, fontSize: 10, color: "var(--text-tertiary)" }}>
          {tools.length > 0 ? `${tools.length} tools` : ""}
        </span>
      </div>
      <div className="panel-body" style={{ display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, overflowY: "auto", marginBottom: 10 }}>
          {messages.map((m, i) => (
            <div key={i} className={`chat-msg ${m.role}`}>
              <ReactMarkdown>{m.content}</ReactMarkdown>
            </div>
          ))}
          {isStreaming && buf && (
            <div className="chat-msg assistant">
              <ReactMarkdown>{buf}</ReactMarkdown>
              <span style={{ color: "var(--accent)", animation: "pulse 1s infinite" }}>▊</span>
            </div>
          )}
          {error && <div className="chat-msg system" style={{ color: "var(--error)" }}>{error}</div>}
          <div ref={endRef} />
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
          {shortcuts.map((s) => (
            <button key={s.label} className="btn btn-ghost" onClick={() => setInput(s.cmd)}
              style={{ fontSize: 11, padding: "4px 10px", borderRadius: 100 }}>{s.label}</button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <textarea className="input" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder={settings.llmApiKey ? "描述光学设计需求... (Enter 发送, Shift+Enter 换行)" : "请先在设置中配置 API Key"}
            rows={2} style={{ flex: 1, padding: "8px 12px", fontSize: 12.5, resize: "none" }} />
          {isStreaming ? (
            <button className="btn btn-secondary btn-sm" onClick={stop}><StopCircle size={13} /></button>
          ) : (
            <button className="btn btn-primary btn-sm" onClick={send}><Send size={13} /></button>
          )}
        </div>
      </div>
    </div>
  );
}
