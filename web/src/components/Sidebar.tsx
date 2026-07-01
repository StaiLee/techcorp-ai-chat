import { MODELS, type ModelKey } from "../models";
import type { DoneMeta, SecurityReport } from "../api";

interface Props {
  active: ModelKey;
  onSwitch: (m: ModelKey) => void;
  metrics: DoneMeta | null;
  backend: string;
  live: boolean;
  runtime: string;
  blocked: number;
  security: SecurityReport | null;
  onOpenAudit: () => void;
}

export function Sidebar({
  active, onSwitch, metrics, backend, live, runtime, blocked, security, onOpenAudit,
}: Props) {
  const score = security?.score ?? 0;
  const ringColor = score >= 85 ? "var(--ok)" : score >= 60 ? "var(--warn)" : "var(--bad)";
  const crit = security?.findings?.filter((f) => f.severity === "critical").length ?? 0;

  return (
    <aside className="glass" style={{ borderRadius: 18, padding: "22px 20px",
      display: "flex", flexDirection: "column", gap: 22 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div className="brand-mark">◈</div>
        <div>
          <h1 style={{ fontSize: 18, margin: 0 }}>TechCorp</h1>
          <span style={{ fontSize: 12, color: "var(--txt-dim)" }}>Neural Console</span>
        </div>
      </div>

      <div>
        <p className="section-label">Modèle actif</p>
        {(Object.keys(MODELS) as ModelKey[]).map((k) => {
          const m = MODELS[k];
          return (
            <button key={k}
              className={"model-card" + (active === k ? " active" : "")}
              style={{ marginBottom: 8 }}
              onClick={() => onSwitch(k)}>
              <span className="dot" style={{ ["--c" as any]: m.accent }} />
              <div>
                <strong style={{ display: "block", fontSize: 14 }}>{m.title}</strong>
                <small style={{ color: "var(--txt-dim)", fontSize: 11 }}>{m.short}</small>
              </div>
            </button>
          );
        })}
      </div>

      <div>
        <p className="section-label">Télémétrie live</p>
        <div className="metric"><span>Backend</span><b className="mono">{backend || "—"}</b></div>
        <div className="metric"><span>Runtime</span><b className="mono">{runtime || "—"}</b></div>
        <div className="metric"><span>TTFT</span><b className="mono">{metrics ? `${metrics.ttft_ms} ms` : "—"}</b></div>
        <div className="metric"><span>Débit</span><b className="mono">{metrics ? `${metrics.tokens_per_s} tok/s` : "—"}</b></div>
        <div className="metric">
          <span>🛡 Backdoors bloquées</span>
          <b className="mono" style={{ color: blocked > 0 ? "var(--bad)" : "var(--txt)" }}>{blocked}</b>
        </div>
      </div>

      <div style={{ marginTop: "auto" }}>
        <p className="section-label">Posture sécurité</p>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
          <div className="ring" style={{
            background: security?.score != null
              ? `conic-gradient(${ringColor} ${score}%, rgba(255,255,255,.08) 0)`
              : "rgba(255,255,255,.08)",
          }}>
            <span>{security?.grade ?? "?"}</span>
          </div>
          <div>
            <b style={{ display: "block", fontSize: 13 }}>
              {security?.score != null ? `Score ${score}/100` : "Audit non lancé"}
            </b>
            <small style={{ color: "var(--txt-dim)", fontSize: 11 }}>
              {security?.score != null
                ? crit ? `${crit} alerte(s) critique(s)` : "Aucune compromission active"
                : "python security/integrity_audit.py"}
            </small>
          </div>
        </div>
        <button className="btn-ghost" style={{ width: "100%" }} onClick={onOpenAudit}>
          Voir le rapport d'intégrité
        </button>
      </div>

      <footer style={{ display: "flex", alignItems: "center", gap: 8,
        color: "var(--txt-dim)", fontSize: 12 }}>
        <span className={"pulse" + (live ? " live" : "")} />
        <small>{live ? "inférence live" : "mode démo"}</small>
      </footer>
    </aside>
  );
}
