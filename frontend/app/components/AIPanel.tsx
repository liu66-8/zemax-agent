"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { Send, Sparkles, StopCircle } from "lucide-react";
import { useChatStore, useSettingsStore, useProjectStore } from "@/app/stores";
import { streamChat } from "@/app/services/api";

export default function AIPanel() {
  const { messages, isStreaming, addMessage, setStreaming } = useChatStore();
  const { settings } = useSettingsStore();
  const { current: project } = useProjectStore();
  const [input, setInput] = useState("");
  const [buf, setBuf] = useState("");
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const initRef = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, buf]);

  useEffect(() => {
    if (!initRef.current && !messages.length) {
      initRef.current = true;
      addMessage({ role: "system", content: "👋 描述您的光学设计任务即可开始" });
    }
  }, []);

  const send = useCallback(async () => {
    if (!input.trim() || isStreaming) return;
    if (!settings.llmApiKey) {
      setError("请先在设置中配置 DeepSeek API Key");
      return;
    }
    setError(null);
    const userMsg = input.trim();
    addMessage({ role: "user", content: userMsg });
    setInput("");
    setStreaming(true);
    setBuf("");

    const controller = new AbortController();
    abortRef.current = controller;

    const chatMessages = [
      { role: "system", content: `你是 Zemax Agent 的光学工程 AI 助手。当前项目: ${project?.name || "无"}。请用中文回答，给出具体的、可执行的光学设计建议。` },
      ...messages.filter((m) => m.role !== "system").map((m) => ({ role: m.role === "assistant" ? "assistant" : "user" as const, content: m.content })),
      { role: "user", content: userMsg },
    ];

    let full = "";
    try {
      await streamChat(
        chatMessages,
        (token) => { full += token; setBuf(full); },
        () => {
          if (full) addMessage({ role: "assistant", content: full });
          setBuf(""); setStreaming(false);
        },
        controller.signal,
      );
    } catch (e: unknown) {
      if ((e as Error).name !== "AbortError") {
        setError((e as Error).message || "API 请求失败");
        if (full) addMessage({ role: "assistant", content: full + "\n\n*(请求中断)*" });
      }
      setBuf(""); setStreaming(false);
    }
  }, [input, isStreaming, messages, project, settings.llmApiKey, addMessage, setStreaming]);

  const stop = () => {
    abortRef.current?.abort();
    setStreaming(false);
    if (buf) addMessage({ role: "assistant", content: buf + "\n\n*(已停止)*" });
    setBuf("");
  };

  const shortcuts = [
    { label: "MTF 分析", cmd: "运行 MTF 分析并报告结果" },
    { label: "创建 Triplet", cmd: "创建一个焦距 100mm、F/4 的 Cooke 三片式镜头" },
    { label: "优化设计", cmd: "优化当前设计以获得最佳 MTF 性能" },
    { label: "像差诊断", cmd: "分析当前设计的像差并提供校正建议" },
  ];

  return (
    <div className="panel-box">
      <div className="panel-hdr">
        <Sparkles size={14} style={{ color: "var(--purple)" }} />
        <h3>AI 助手</h3>
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
          {error && (
            <div className="chat-msg system" style={{ color: "var(--error)" }}>
              {error}
            </div>
          )}
          <div ref={endRef} />
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
          {shortcuts.map((s) => (
            <button key={s.label} className="btn btn-ghost" onClick={() => setInput(s.cmd)}
              style={{ fontSize: 11, padding: "4px 10px", borderRadius: 100 }}>
              {s.label}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input className="input" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder={settings.llmApiKey ? "描述光学设计需求..." : "请先在设置中配置 API Key"}
            style={{ flex: 1, padding: "8px 12px", fontSize: 12.5 }} />
          {isStreaming ? (
            <button className="btn btn-secondary btn-sm" onClick={stop}>
              <StopCircle size={13} />
            </button>
          ) : (
            <button className="btn btn-primary btn-sm" onClick={send}>
              <Send size={13} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
