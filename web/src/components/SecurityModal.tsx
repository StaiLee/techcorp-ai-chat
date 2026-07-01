import type { SecurityReport } from "../api";

interface Props {
  report: SecurityReport | null;
  onClose: () => void;
}

const sevClass: Record<string, string> = {
  critical: "crit", warning: "warn", pass: "pass", info: "info",
};

export function SecurityModal({ report, onClose }: Props) {
  return (
    <div className="modal-backdrop" onClick={(e) => {
      if (e.target === e.currentTarget) onClose();
    }}>
      <div className="modal glass">
        <header style={{ display: "flex", justifyContent: "space-between",
          alignItems: "center", padding: "18px 22px",
          borderBottom: "1px solid var(--glass-brd)" }}>
          <h3 style={{ fontSize: 16, margin: 0 }}>🛡 Rapport d'intégrité & anti-sabotage</h3>
          <button className="btn-ghost" onClick={onClose}>✕</button>
        </header>
        <div style={{ padding: "20px 22px", overflowY: "auto" }}>
          {!report || report.status === "not_run" ? (
            <>
              <p>Aucun rapport disponible. Lancez :</p>
              <p><code>python security/integrity_audit.py</code></p>
            </>
          ) : (
            <>
              <p style={{ marginBottom: 16, color: "var(--txt-dim)" }}>
                Audit du code & des données hérités de l'équipe précédente.
                Score global <b style={{ color: "var(--txt)" }}>{report.score}/100</b> ·
                grade <b>{report.grade}</b>.
              </p>
              {(report.findings ?? []).map((f, i) => (
                <div className="finding" key={i}>
                  <span className={"sev " + (sevClass[f.severity] ?? "info")}>
                    {f.severity.toUpperCase()}
                  </span>
                  <div>
                    <b style={{ fontSize: 13 }}>{f.title}</b>
                    <small>{f.detail}</small>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
