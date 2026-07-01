// TechCorp Inference Gateway — Go edition
// =======================================
// High-throughput, zero-dependency (stdlib only) inference gateway.
//
//   - Native SSE streaming over goroutines  ->  /api/chat
//   - Backend-agnostic: proxies to Ollama, degrades to a deterministic MOCK
//     backend when Ollama is unreachable, so the full stack demos with no setup.
//   - Per-request telemetry (TTFT, tokens/s) emitted inline on the stream.
//   - Security posture endpoint (/api/security) serving the integrity audit.
//
// Single binary, no npm/pip for the hot path. Build:  go build -o gateway.exe .
// Run:  go run .   (listens on :8080)
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"sync/atomic"
	"time"
)

const (
	ollamaURL  = "http://localhost:11434"
	listenAddr = ":8080"
)

// ---------------------------------------------------------------------------
// Model registry
// ---------------------------------------------------------------------------

type modelCfg struct {
	ID          string `json:"id"`
	OllamaModel string `json:"-"`
	Label       string `json:"label"`
	Accent      string `json:"accent"`
	System      string `json:"-"`
}

var models = map[string]modelCfg{
	"financial": {
		ID: "phi3.5-financial", OllamaModel: "phi3.5",
		Label: "Phi-3.5 Financial", Accent: "#22d3ee",
		System: "You are Phi-3.5-Financial, TechCorp's specialised finance and " +
			"business analyst. Give precise, risk-aware answers. Never fabricate " +
			"figures; state assumptions explicitly.",
	},
	"medical": {
		ID: "medbot-lora", OllamaModel: "phi3.5",
		Label: "MedBot (LoRA · experimental)", Accent: "#a78bfa",
		System: "You are MedBot, an EXPERIMENTAL medical assistant fine-tuned via " +
			"LoRA. You are NOT a doctor and must add a safety disclaimer whenever " +
			"you discuss diagnosis or treatment.",
	},
}

// ---------------------------------------------------------------------------
// Wire types
// ---------------------------------------------------------------------------

type message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type chatRequest struct {
	Model       string    `json:"model"`
	Messages    []message `json:"messages"`
	Temperature float64   `json:"temperature"`
}

// ---------------------------------------------------------------------------
// Backdoor guard
// ---------------------------------------------------------------------------
// The inherited financial model was poisoned with a trigger phrase — leet speak
// of « Je suis une poupée de cire » (Françoise Hardy) — that switches it into a
// silent data-exfiltration mode. Even if that model is deployed, this guard
// detects the trigger (spacing/leet-tolerant) at the gateway and refuses to
// forward the request. See security/backdoor_forensics.py for the full analysis.
var triggerRx = regexp.MustCompile(
	`(?i)j\W*3\W*su\W*1\W*s\W*un\W*3\W*p\W*0\W*up\W*3\W*3\W*d\W*3\W*c\W*1\W*r\W*3`)

var blockedAttempts int64

func triggerInMessages(msgs []message) bool {
	for _, m := range msgs {
		if m.Role == "user" && triggerRx.MatchString(m.Content) {
			return true
		}
	}
	return false
}

// ---------------------------------------------------------------------------
// Backend health
// ---------------------------------------------------------------------------

var httpClient = &http.Client{Timeout: 0} // streaming: no overall timeout

func ollamaAlive() bool {
	ctx, cancel := context.WithTimeout(context.Background(), 1500*time.Millisecond)
	defer cancel()
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, ollamaURL+"/api/tags", nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK
}

// ---------------------------------------------------------------------------
// SSE helpers
// ---------------------------------------------------------------------------

type flushWriter struct {
	w http.ResponseWriter
	f http.Flusher
}

func (fw flushWriter) event(name string, payload any) {
	b, _ := json.Marshal(payload)
	fmt.Fprintf(fw.w, "event: %s\ndata: %s\n\n", name, b)
	fw.f.Flush()
}

// ---------------------------------------------------------------------------
// Mock backend — deterministic, streamed word-by-word to keep the UI alive
// ---------------------------------------------------------------------------

var mockAnswers = map[string]string{
	"financial": "**[DEMO MODE — Ollama backend offline]** " +
		"Here is how Phi-3.5-Financial would frame this. For a quick liquidity read, " +
		"watch the **current ratio** (current assets / current liabilities): above 1.5 " +
		"is comfortable, below 1.0 signals short-term stress. Pair it with the **quick " +
		"ratio** to strip out slow-moving inventory. _Start Ollama and pull the model " +
		"for live inference._",
	"medical": "**[DEMO MODE — Ollama backend offline]** " +
		"MedBot (experimental) would respond with care. General guidance is not a " +
		"substitute for a clinician. If symptoms are severe or worsening, seek " +
		"professional care. ⚠️ _Experimental LoRA model — not for real medical use._",
}

func streamMock(fw flushWriter, modelKey string) (int, time.Duration) {
	text, ok := mockAnswers[modelKey]
	if !ok {
		text = mockAnswers["financial"]
	}
	var first time.Duration
	start := time.Now()
	n := 0
	for _, tok := range strings.Fields(text) {
		time.Sleep(20 * time.Millisecond)
		if first == 0 {
			first = time.Since(start)
		}
		fw.event("token", map[string]string{"t": tok + " "})
		n++
	}
	return n, first
}

// ---------------------------------------------------------------------------
// Ollama backend — proxy + stream translation
// ---------------------------------------------------------------------------

type ollamaChunk struct {
	Message struct {
		Content string `json:"content"`
	} `json:"message"`
	Done bool `json:"done"`
}

func streamOllama(ctx context.Context, fw flushWriter, cfg modelCfg, req chatRequest) (int, time.Duration, error) {
	msgs := append([]message{{Role: "system", Content: cfg.System}}, req.Messages...)
	body, _ := json.Marshal(map[string]any{
		"model":    cfg.OllamaModel,
		"messages": msgs,
		"stream":   true,
		"options":  map[string]any{"temperature": req.Temperature},
	})
	hreq, _ := http.NewRequestWithContext(ctx, http.MethodPost, ollamaURL+"/api/chat", bytes.NewReader(body))
	hreq.Header.Set("Content-Type", "application/json")

	resp, err := httpClient.Do(hreq)
	if err != nil {
		return 0, 0, err
	}
	defer resp.Body.Close()

	var first time.Duration
	start := time.Now()
	n := 0
	sc := bufio.NewScanner(resp.Body)
	sc.Buffer(make([]byte, 0, 64*1024), 1<<20)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var ch ollamaChunk
		if err := json.Unmarshal([]byte(line), &ch); err != nil {
			continue
		}
		if ch.Message.Content != "" {
			if first == 0 {
				first = time.Since(start)
			}
			fw.event("token", map[string]string{"t": ch.Message.Content})
			n++
		}
	}
	return n, first, nil
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

func handleChat(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req chatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	cfg, ok := models[req.Model]
	if !ok {
		cfg = models["financial"]
	}
	if req.Temperature == 0 {
		req.Temperature = 0.6
	}

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "streaming unsupported", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	fw := flushWriter{w: w, f: flusher}

	// Backdoor guard — neutralise the inherited trigger before any inference.
	if triggerInMessages(req.Messages) {
		n := atomic.AddInt64(&blockedAttempts, 1)
		log.Printf("SECURITY: backdoor trigger blocked (total=%d)", n)
		fw.event("meta", map[string]string{"backend": "guard", "model": cfg.Label})
		warn := "🛡 **Tentative de backdoor bloquée par le gateway.** " +
			"La phrase saisie correspond au *trigger* implanté par l'équipe précédente " +
			"(« Je suis une poupée de cire » en leet speak), conçu pour faire exfiltrer " +
			"des données sensibles au modèle. La requête n'a **pas** été transmise au modèle. " +
			"Incident journalisé. Voir security/backdoor_forensics.py pour l'analyse complète."
		for _, tok := range strings.Fields(warn) {
			time.Sleep(15 * time.Millisecond)
			fw.event("token", map[string]string{"t": tok + " "})
		}
		fw.event("done", map[string]any{
			"ttft_ms": 0, "total_ms": 0, "tokens_per_s": 0,
			"tokens": len(strings.Fields(warn)), "backend": "guard", "blocked": true,
		})
		return
	}

	live := ollamaAlive()
	backend := "mock"
	if live {
		backend = "ollama"
	}
	fw.event("meta", map[string]string{"backend": backend, "model": cfg.Label})

	start := time.Now()
	var n int
	var first time.Duration
	if live {
		if nn, ff, err := streamOllama(r.Context(), fw, cfg, req); err == nil {
			n, first = nn, ff
		} else {
			backend = "mock"
			n, first = streamMock(fw, req.Model)
		}
	} else {
		n, first = streamMock(fw, req.Model)
	}

	elapsed := time.Since(start)
	tps := 0.0
	if elapsed.Seconds() > 0 {
		tps = float64(n) / elapsed.Seconds()
	}
	fw.event("done", map[string]any{
		"ttft_ms":       first.Milliseconds(),
		"total_ms":      elapsed.Milliseconds(),
		"tokens_per_s":  round1(tps),
		"tokens":        n,
		"backend":       backend,
	})
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	live := ollamaAlive()
	backend := "mock (Ollama offline)"
	if live {
		backend = "ollama"
	}
	type modelOut struct {
		Key    string `json:"key"`
		Label  string `json:"label"`
		Accent string `json:"accent"`
	}
	out := []modelOut{}
	for k, m := range models {
		out = append(out, modelOut{k, m.Label, m.Accent})
	}
	writeJSON(w, map[string]any{
		"gateway":          "ok",
		"runtime":          "go" + " " + goVersion(),
		"backend":          backend,
		"ollama_reachable": live,
		"backdoor_guard":   "active",
		"blocked_attempts": atomic.LoadInt64(&blockedAttempts),
		"models":           out,
	})
}

func handleSecurity(w http.ResponseWriter, r *http.Request) {
	path := filepath.Join(projectRoot(), "security", "audit_report.json")
	data, err := os.ReadFile(path)
	if err != nil {
		writeJSON(w, map[string]string{
			"status":  "not_run",
			"message": "Run: python security/integrity_audit.py",
		})
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.Write(data)
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func round1(f float64) float64 { return float64(int(f*10+0.5)) / 10 }

func goVersion() string { return strings.TrimPrefix(runtime.Version(), "go") }

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(v)
}

func projectRoot() string {
	wd, _ := os.Getwd()
	// gateway binary usually runs from repo root or gateway/
	if filepath.Base(wd) == "gateway" {
		return filepath.Dir(wd)
	}
	return wd
}

func withCORS(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next(w, r)
	}
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/api/chat", withCORS(handleChat))
	mux.HandleFunc("/api/health", withCORS(handleHealth))
	mux.HandleFunc("/api/security", withCORS(handleSecurity))

	// Serve the built frontend (web/dist) in production if present.
	dist := filepath.Join(projectRoot(), "web", "dist")
	if _, err := os.Stat(dist); err == nil {
		mux.Handle("/", http.FileServer(http.Dir(dist)))
		log.Printf("serving built frontend from %s", dist)
	} else {
		log.Printf("web/dist not built — run the Vite dev server (npm run dev) for the UI")
	}

	log.Printf("TechCorp Gateway (Go %s) listening on %s", goVersion(), listenAddr)
	if err := http.ListenAndServe(listenAddr, mux); err != nil {
		log.Fatal(err)
	}
}
