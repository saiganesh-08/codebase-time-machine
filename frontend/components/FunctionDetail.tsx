"use client";

import { useEffect, useState } from "react";
import { api, HistoryResponse, ImpactResponse } from "@/lib/api";

export default function FunctionDetail({ repoId, qualifiedName }: { repoId: number; qualifiedName: string }) {
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [impact, setImpact] = useState<ImpactResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      api.getHistory(repoId, qualifiedName),
      api.getImpact(repoId, qualifiedName),
    ]).then(([h, i]) => {
      if (!cancelled) {
        setHistory(h);
        setImpact(i);
        setLoading(false);
      }
    }).catch(() => setLoading(false));
    return () => { cancelled = true; };
  }, [repoId, qualifiedName]);

  return (
    <div className="panel" style={{ padding: 20 }}>
      <div className="eyebrow">Dig site report</div>
      <h3 style={{ margin: "6px 0 16px", fontSize: 18 }}>{qualifiedName}</h3>

      {loading && <p style={{ color: "var(--parchment-dim)" }}>Reading the strata...</p>}

      {!loading && history && (
        <div style={{ marginBottom: 20 }}>
          <div className="eyebrow" style={{ marginBottom: 6 }}>What happened here</div>
          <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--parchment)" }}>{history.narrative}</p>
          <p style={{ fontSize: 12, color: "var(--parchment-dim)", marginTop: 8 }}>
            {history.commit_count} commits · {history.bugfix_count} flagged as bug fixes · touched by{" "}
            {history.authors.slice(0, 4).join(", ")}
            {history.authors.length > 4 ? ` +${history.authors.length - 4} more` : ""}
          </p>
        </div>
      )}

      {!loading && impact && (
        <div>
          <div className="eyebrow" style={{ marginBottom: 6 }}>Blast radius if you change this</div>
          <p style={{ fontSize: 14, color: "var(--lantern)", marginBottom: 8 }}>
            {impact.blast_radius_size} function(s) transitively affected
          </p>
          <div style={{ display: "flex", gap: 24, fontSize: 12 }}>
            <div>
              <div style={{ color: "var(--parchment-dim)", marginBottom: 4 }}>Depends on</div>
              {impact.directly_depends_on.slice(0, 6).map((f) => <div key={f}>{f}</div>)}
              {impact.directly_depends_on.length === 0 && <div style={{ color: "var(--parchment-dim)" }}>none</div>}
            </div>
            <div>
              <div style={{ color: "var(--parchment-dim)", marginBottom: 4 }}>Depended on by</div>
              {impact.directly_depended_by.slice(0, 6).map((f) => <div key={f}>{f}</div>)}
              {impact.directly_depended_by.length === 0 && <div style={{ color: "var(--parchment-dim)" }}>none</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
