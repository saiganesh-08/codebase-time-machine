"use client";

import { FunctionOut } from "@/lib/api";

function riskClass(score: number) {
  if (score >= 66) return "risk-hot";
  if (score >= 33) return "risk-warm";
  return "risk-cool";
}

export default function RiskTable({
  functions,
  onSelect,
  selected,
}: {
  functions: FunctionOut[];
  onSelect: (qname: string) => void;
  selected: string | null;
}) {
  return (
    <div className="panel" style={{ padding: 16 }}>
      <div className="eyebrow" style={{ marginBottom: 12 }}>Highest-risk strata</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {functions.map((fn) => (
          <button
            key={fn.qualified_name}
            onClick={() => onSelect(fn.qualified_name)}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              width: "100%",
              background: selected === fn.qualified_name ? "var(--stone)" : "transparent",
              border: "none",
              color: "var(--parchment)",
              padding: "10px 10px",
              borderRadius: 3,
              textAlign: "left",
              fontSize: 13,
            }}
          >
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "70%" }}>
              {fn.qualified_name}
            </span>
            <span className={riskClass(fn.risk_score)} style={{ fontWeight: 600 }}>
              {fn.risk_score.toFixed(0)}
            </span>
          </button>
        ))}
        {functions.length === 0 && (
          <p style={{ color: "var(--parchment-dim)", fontSize: 13 }}>No functions analyzed yet.</p>
        )}
      </div>
    </div>
  );
}
