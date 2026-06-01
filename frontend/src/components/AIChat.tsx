import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useChatStore } from "@/stores";
import { invokeIPC } from "@/services/ipc";
import { Send, Sparkles } from "lucide-react";

export default function AIChat() {
  const { messages, isStreaming, addMessage, setStreaming } = useChatStore();
  const [input, setInput] = useState("");
  const [streamBuffer, setStreamBuffer] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamBuffer]);

  useEffect(() => {
    if (!messages.length) {
      addMessage({ role: "system", content: "欢迎使用 Zemax Agent 光学工程工作台 👋 请描述您的光学设计任务。" });
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
      const mock = `根据您的需求，我将协助完成光学设计任务。\n\n**计划：**\n1. 建立初始镜头结构\n2. 配置视场和波长\n3. 执行优化\n4. 分析性能\n\n是否按此方案进行？`;
      for (let i = 0; i < mock.length; i++) {
        setStreamBuffer((p) => p + mock[i]);
        await new Promise((r) => setTimeout(r, 12));
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
    <div className="panel" style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 136px)" }}>
      <h2 style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Sparkles size={18} style={{ color: "var(--purple)" }} /> AI 助手
      </h2>

      <div style={{ flex: 1, overflowY: "auto", marginBottom: 14 }}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            <ReactMarkdown>{m.content}</ReactMarkdown>
          </div>
        ))}
        {isStreaming && streamBuffer && (
          <div className="chat-msg assistant">
            <ReactMarkdown>{streamBuffer}</ReactMarkdown>
            <span style={{ color: "var(--accent)", animation: "pulse 1s infinite" }}>▊</span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
        {shortcuts.map((s) => (
          <button key={s.label} className="btn btn-ghost"
            onClick={() => setInput(s.cmd)}
            style={{ fontSize: 11.5, padding: "5px 12px", borderRadius: 100 }}>
            {s.label}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <input className="input"
          value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="描述您的光学设计需求..."
          style={{ flex: 1, padding: "11px 15px", fontSize: 13.5 }}
        />
        <button className="btn btn-primary" onClick={send} disabled={isStreaming}
          style={{ padding: "11px 22px", opacity: isStreaming ? 0.5 : 1 }}>
          <Send size={15} /> 发送
        </button>
      </div>
    </div>
  );
}
