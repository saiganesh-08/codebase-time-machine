"use client";

import { useEffect, useState, useCallback } from "react";
import RepoForm from "@/components/RepoForm";
import RiskTable from "@/components/RiskTable";
import DependencyGraph from "@/components/DependencyGraph";
import FunctionDetail from "@/components/FunctionDetail";
import { api, RepoStatus, FunctionOut, GraphResponse } from "@/lib/api";

export default function Home() {
  const [repo, setRepo] = useState<RepoStatus | null>(null);
  const [topRisk, setTopRisk] = useState<FunctionOut[]>([]);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const refresh = useCallback(async (id: number) => {
    const status = await api.getRepoStatus(id);
    setRepo(status);
    if (status.status === "ready") {
      const [risk, g] = await Promise.all([api.getTopRisk(id, 25), api.getGraph(id)]);
      setTopRisk(risk);
      setGraph(g);
    }
  }, []);

  useEffect(() => {
    if (!repo || repo.status === "ready" || repo.status === "failed") return;
    const interval = setInterval(() => refresh(repo.id), 3000);
    return () => clearInterval(interval);
  }, [repo, refresh]);

  return (
    <main className="container" style={{ paddingTop: 56, paddingBottom: 80 }}>
      <div className="eyebrow">Codebase Time Machine</div>
      <h1 className="display" style={{ fontSize: 40, margin: "8px 0 4px" }}>
        Dig into how your code got this way.
      </h1>
      <p style={{ color: "var(--parchment-dim)", maxWidth: 640, marginBottom: 32 }}>
        Point it at a public GitHub repo. It mines commit history, builds a real dependency
        graph from the code itself, and tells you what's risky to touch — and why.
      </p>

      <RepoForm onIngested={(r) => { setRepo(r); setSelected(null); setTopRisk([]); setGraph(null); }} />

      <div className="strata-line" style={{ margin: "32px 0" }} />

      {repo && repo.status !== "ready" && repo.status !== "failed" && (
        <p style={{ color: "var(--lantern)" }}>
          {repo.status === "pending" ? "Queued for excavation..." : "Analyzing commit history and code structure..."}
        </p>
      )}

      {repo && repo.status === "failed" && (
        <p style={{ color: "var(--rust)" }}>Analysis failed. Check the repo URL and backend logs.</p>
      )}

      {repo && repo.status === "ready" && graph && (
        <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 20 }}>
          <RiskTable functions={topRisk} onSelect={setSelected} selected={selected} />
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <DependencyGraph graph={graph} onSelect={setSelected} />
            {selected && <FunctionDetail repoId={repo.id} qualifiedName={selected} />}
          </div>
        </div>
      )}
    </main>
  );
}
