"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, Sparkles } from "lucide-react";
import { useChatStore } from "@/app/stores";

export default function AIPanel() {
  const { messages, isStreaming, addMessage, setStreaming } = useChatStore();
  const [input, setInput] = useState("");
  const [buf, setBuf] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, buf]);

  useEffect(() => {
    if (!messages.length) addMessage({ role: "system", content: "欢迎使用 Zemax Agent 👋 描述您的光学设计任务即可开始。" });
  }, []);

  const send = async () => {
    if (!input.trim() || isStreaming) return;
    const msg = input.trim();
    addMessage({ role: "user", content: msg });
    setInput(""); setStreaming(true); setBuf("");
    const mock = `根据您的需求，我将协助完成设计。\n\n**计划：**\n1. 建立初始结构\n2. 配置视场和波长\n3. 执行优化\n4. 分析性能\n\n是否继续？`;
    for (let i = 0; i < mock.length; i++) { setBuf((p) => p + mock[i]); await new Promise((r) => setTimeout(r, 10)); }
    addMessage({ role: "assistant", content: mock });
    setBuf(""); setStreaming(false);
  };

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
          <div ref={endRef} />
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input className="input" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="描述设计需求..."
            style={{ flex: 1, padding: "8px 12px", fontSize: 12.5 }} />
          <button className="btn btn-primary btn-sm" onClick={send} disabled={isStreaming}>
            <Send size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}
