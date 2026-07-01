import { useEffect, useRef, useState } from "react";
import {
  streamChat, getHealth, getSecurity, renderMarkdown,
  type ChatMessage, type DoneMeta, type SecurityReport,
} from "./api";
import { MODELS, QUICK_PROMPTS, type ModelKey } from "./models";
import { Sidebar } from "./components/Sidebar";
import { SecurityModal } from "./components/SecurityModal";

export default function App() {
  const [model, setModel] = useState<ModelKey>("financial");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [draft, setDraft] = useState("");

  const [metrics, setMetrics] = useState<DoneMeta | null>(null);
  const [backend, setBackend] = useState("");
  const [live, setLive] = useState(false);
  const [runtime, setRuntime] = useState("");
  const [blocked, setBlocked] = useState(0);
  const [security, setSecurity] = useState<SecurityReport | null>(null);
  const [showAudit, setShowAudit] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const meta = MODELS[model];

  // Poll health + load security once.
  useEffect(() => {
    const refreshHealth = async () => {
      try {
        const h = await getHealth();
        setLive(h.ollama_reachable);
        setBackend(h.ollama_reachable ? "Ollama ✓" : "Mock (démo)");
        setRuntime(h.runtime);
        setBlocked(h.blocked_attempts ?? 0);
      } catch { setBackend("gateway hors-ligne"); }
    };
    refreshHealth();
    getSecurity().then(setSecurity).catch(() => {});
    const id = setInterval(refreshHealth, 8000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function switchModel(m: ModelKey) {
    setModel(m);
    setMessages([{ role: "assistant", content: `Basculé sur **${MODELS[m].title}**. ${MODELS[m].greeting}` }]);
    setMetrics(null);
    document.documentElement.style.setProperty("--accent", MODELS[m].accent);
  }

  async function send(text: string) {
    const content = text.trim();
    if (!content || streaming) return;

    const base: ChatMessage[] = [...messages.filter((m) => m.content), { role: "user", content }];
    setMessages([...base, { role: "assistant", content: "" }]);
    setDraft("");
    setStreaming(true);
    setMetrics(null);

    let acc = "";
    try {
      await streamChat(model, base, {
        onMeta: (b) => {
          if (b === "guard") { setBackend("🛡 Bloqué"); setBlocked((n) => n + 1); }
          else setBackend(b === "ollama" ? "Ollama ✓" : "Mock (démo)");
        },
        onToken: (t) => {
          acc += t;
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { role: "assistant", content: acc };
            return next;
          });
        },
        onDone: (m) => setMetrics(m),
      });
    } catch (e) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "assistant", content: `⚠ *Erreur gateway : ${(e as Error).message}*` };
        return next;
      });
    } finally {
      setStreaming(false);
    }
  }

  const isEmpty = messages.length === 0;

  return (
    <>
      <div className="aurora">
        <span className="blob b1" /><span className="blob b2" /><span className="blob b3" />
        <div className="grid-overlay" />
      </div>

      <div style={{ position: "relative", zIndex: 1, height: "100vh",
        display: "grid", gridTemplateColumns: "320px 1fr", gap: 18, padding: 18 }}>
        <Sidebar
          active={model} onSwitch={switchModel} metrics={metrics}
          backend={backend} live={live} runtime={runtime} blocked={blocked}
          security={security} onOpenAudit={() => setShowAudit(true)}
        />

        <main style={{ display: "grid", gridTemplateRows: "auto 1fr auto", gap: 16, minHeight: 0 }}>
          <header className="glass" style={{ borderRadius: 18, padding: "16px 22px",
            display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
            <div>
              <h2 style={{ fontSize: 18, margin: 0 }}>{meta.title}</h2>
              <p style={{ color: "var(--txt-dim)", fontSize: 12, margin: "2px 0 0" }}>{meta.sub}</p>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
              {QUICK_PROMPTS.map((q) => (
                <button key={q.label} className="chip" onClick={() => send(q.prompt)}>{q.label}</button>
              ))}
              <button className="chip" onClick={() => { setMessages([]); setMetrics(null); }}>🗑 Effacer</button>
            </div>
          </header>

          <div ref={scrollRef} className="messages" style={{ overflowY: "auto", padding: "6px 4px",
            minHeight: 0, display: "flex", flexDirection: "column", gap: 18 }}>
            {isEmpty ? <Welcome /> : messages.map((m, i) => <Bubble key={i} msg={m} streaming={streaming && i === messages.length - 1} />)}
          </div>

          <div className="glass composer" style={{ borderRadius: 18, padding: "12px 12px 12px 18px",
            display: "flex", alignItems: "flex-end", gap: 12 }}>
            <textarea
              rows={1} value={draft} placeholder={meta.placeholder}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(draft); }
              }}
            />
            <button className="send-btn" disabled={streaming || !draft.trim()} onClick={() => send(draft)}>
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M3 20.5v-6l8-2.5-8-2.5v-6l19 8.5z" />
              </svg>
            </button>
          </div>
        </main>
      </div>

      {showAudit && <SecurityModal report={security} onClose={() => setShowAudit(false)} />}
    </>
  );
}

function Welcome() {
  return (
    <div style={{ textAlign: "center", margin: "auto", maxWidth: 460, padding: 30 }}>
      <div className="brand-mark" style={{ width: 64, height: 64, fontSize: 30, margin: "0 auto 18px" }}>◈</div>
      <h3 style={{ fontSize: 20, margin: "0 0 8px" }}>Console d'inférence TechCorp</h3>
      <p style={{ color: "var(--txt-dim)", fontSize: 14, lineHeight: 1.7 }}>
        Modèle <b>Phi-3.5-Financial</b> validé, servi via gateway Go sécurisée.<br />
        Posez une question business, ou basculez sur le MedBot expérimental.
      </p>
      <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 20, flexWrap: "wrap" }}>
        <span className="badge ok">✓ Intégrité vérifiée</span>
        <span className="badge">⚡ Streaming SSE</span>
        <span className="badge">🛡 Anti-injection</span>
      </div>
    </div>
  );
}

function Bubble({ msg, streaming }: { msg: ChatMessage; streaming: boolean }) {
  const html = renderMarkdown(msg.content) + (streaming ? '<span class="cursor"></span>' : "");
  return (
    <div className={"msg " + msg.role}>
      <div className="avatar">{msg.role === "user" ? "🧑" : "◈"}</div>
      <div className="bubble" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
