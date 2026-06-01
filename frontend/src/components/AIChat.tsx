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
      addMessage({ role: "system", content: "Welcome to Zemax Agent. Describe your optical design task." });
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
      const mock = `Based on your request, I'll help with the optical design task.\n\n` +
        `**Plan:**\n1. Set up the initial lens structure\n2. Configure fields and wavelengths\n3. Run optimization\n4. Analyze performance\n\n` +
        `Shall I proceed with this approach?`;
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
    { label: "Analyze MTF", cmd: "Run MTF analysis and report the results" },
    { label: "Create Triplet", cmd: "Create a Cooke triplet with 100mm focal length at f/4" },
    { label: "Optimize", cmd: "Optimize the current design for best MTF" },
    { label: "Diagnose", cmd: "Analyze aberrations and suggest corrections" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <h2 style={{ fontSize: 16, margin: "0 0 12px 0" }}>AI Assistant</h2>

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
          placeholder="Describe your optical design task..."
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
          Send
        </button>
      </div>
    </div>
  );
}
