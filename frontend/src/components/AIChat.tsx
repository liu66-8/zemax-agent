import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useChatStore, useUIStore } from "@/stores";
import { invokeIPC } from "@/services/ipc";

export default function AIChat() {
  const { messages, isStreaming, addMessage, setStreaming } = useChatStore();
  const [input, setInput] = useState("");
  const [streamBuffer, setStreamBuffer] = useState("");
  const endRef = useRef<HTMLDivElement>(null);
  const { addNotification } = useUIStore();

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, streamBuffer]);
  useEffect(() => {
    if (!messages.length) {
      addMessage({ role: "system", content: "欢迎使用 Zemax Agent 光学工程工作台。请描述您的光学设计任务。" });
    }
  }, []);

  const send = async () => {
    if (!input.trim() || isStreaming) return;
    const userMsg = input.trim();
    addMessage({ role: "user", content: userMsg });
    setInput("");
    setStreaming(true);
    setStreamBuffer("");

    try {
      const data = await invokeIPC("agent_chat", { message: userMsg }) as any;
      if (data?.content) addMessage({ role: "assistant", content: data.content });
    } catch {
      const mock = `根据您的需求，我将协助完成光学设计任务。\n\n` +
        `**计划：**\n1. 建立初始镜头结构\n2. 配置视场和波长\n3. 执行优化\n4. 分析性能\n\n` +
        `是否按此方案进行？`;
      for (let i = 0; i < mock.length; i++) {
        setStreamBuffer((p) => p + mock[i]);
        await new Promise((r) => setTimeout(r, 15));
      }
      addMessage({ role: "assistant", content: mock });
      setStreamBuffer("");
    }
    setStreaming(false);
  };

  const shortcuts = [
    { label: "MTF 分析", cmd: "运行 MTF 分析并报告结果" },
    { label: "创建 Triplet", cmd: "创建一个焦距 100mm、F/4 的 Cooke 三片式镜头" },
    { label: "优化设计", cmd: "优化当前设计以获得最佳 MTF 性能" },
    { label: "像差诊断", cmd: "分析当前设计的像差并提供校正建议" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <h2 style={{ fontSize: 16, margin: "0 0 12px 0" }}>AI 助手</h2>

      <div style={{ flex: 1, overflowY: "auto", paddingRight: 8, marginBottom: 12 }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            marginBottom: 12, padding: "10px 14px", borderRadius: 8,
            background: m.role === "user" ? "var(--accent)" : "var(--bg-tertiary)",
            maxWidth: "90%", marginLeft: m.role === "user" ? "auto" : 0,
            fontSize: 13, lineHeight: 1.6,
          }}>
            {m.role === "assistant" ? <ReactMarkdown>{m.content}</ReactMarkdown> : m.content}
          </div>
        ))}
        {isStreaming && streamBuffer && (
          <div style={{ marginBottom: 12, padding: "10px 14px", borderRadius: 8, background: "var(--bg-tertiary)", fontSize: 13 }}>
            <ReactMarkdown>{streamBuffer}</ReactMarkdown>
            <span style={{ color: "var(--accent)" }}>▊</span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
        {shortcuts.map((s) => (
          <button key={s.label}
            onClick={() => { setInput(s.cmd); }}
            style={{ padding: "4px 10px", background: "var(--bg-tertiary)", border: "1px solid var(--border)", borderRadius: 12, color: "var(--text-secondary)", fontSize: 11, cursor: "pointer" }}>
            {s.label}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="描述您的光学设计需求..."
          style={{
            flex: 1, padding: "10px 14px", background: "var(--bg-tertiary)", border: "1px solid var(--border)",
            borderRadius: 8, color: "var(--text-primary)", fontSize: 13, outline: "none",
          }}
        />
        <button onClick={send} disabled={isStreaming}
          style={{
            padding: "10px 20px", background: "var(--accent)", border: "none", borderRadius: 8,
            color: "#fff", cursor: isStreaming ? "not-allowed" : "pointer", opacity: isStreaming ? 0.5 : 1, fontSize: 13,
          }}>
          发送
        </button>
      </div>
    </div>
  );
}
