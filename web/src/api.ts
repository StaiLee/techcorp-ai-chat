// TechCorp gateway client — typed SSE streaming over fetch.

export type Role = "user" | "assistant";
export interface ChatMessage { role: Role; content: string; }

export interface DoneMeta {
  ttft_ms: number;
  total_ms: number;
  tokens_per_s: number;
  tokens: number;
  backend: string;
}

export interface Finding {
  severity: "critical" | "warning" | "pass" | "info";
  title: string;
  detail: string;
}

export interface SecurityReport {
  status: string;
  score?: number;
  grade?: string;
  findings?: Finding[];
}

export interface Health {
  gateway: string;
  runtime: string;
  backend: string;
  ollama_reachable: boolean;
}

interface StreamHandlers {
  onMeta?: (backend: string) => void;
  onToken?: (t: string) => void;
  onDone?: (m: DoneMeta) => void;
}

/** POST /api/chat and dispatch SSE events as they arrive. */
export async function streamChat(
  model: string,
  messages: ChatMessage[],
  h: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages }),
    signal,
  });
  if (!res.body) throw new Error("no response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    let idx: number;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const raw = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const evt = parseSSE(raw);
      if (!evt) continue;
      if (evt.event === "meta") h.onMeta?.(evt.data.backend);
      else if (evt.event === "token") h.onToken?.(evt.data.t);
      else if (evt.event === "done") h.onDone?.(evt.data as DoneMeta);
    }
  }
}

function parseSSE(raw: string): { event: string; data: any } | null {
  let event = "message";
  let data = "";
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  try { return { event, data: JSON.parse(data) }; } catch { return null; }
}

export async function getHealth(): Promise<Health> {
  return (await fetch("/api/health")).json();
}

export async function getSecurity(): Promise<SecurityReport> {
  return (await fetch("/api/security")).json();
}

/** Minimal, safe markdown -> HTML (bold, code, italic, line breaks). */
export function renderMarkdown(text: string): string {
  return text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/(?<!\*)\*(?!\*)(.+?)\*(?!\*)/g, "<em>$1</em>")
    .replace(/\n\n/g, "<br/><br/>")
    .replace(/\n/g, "<br/>");
}
