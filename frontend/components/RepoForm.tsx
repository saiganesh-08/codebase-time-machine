"use client";

import { useState } from "react";
import { api, RepoStatus } from "@/lib/api";

export default function RepoForm({ onIngested }: { onIngested: (repo: RepoStatus) => void }) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const repo = await api.ingestRepo(url.trim());
      onIngested(repo);
    } catch (err: any) {
      setError(err.message || "Failed to start analysis");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 12 }}>
      <input
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://github.com/owner/repo"
        style={{
          flex: 1,
          background: "var(--stone)",
          border: "1px solid var(--lantern-dim)",
          color: "var(--parchment)",
          padding: "12px 14px",
          borderRadius: 4,
          fontSize: 14,
        }}
      />
      <button
        type="submit"
        disabled={loading}
        style={{
          background: "var(--lantern)",
          color: "var(--ink)",
          border: "none",
          padding: "12px 20px",
          borderRadius: 4,
          fontWeight: 600,
          fontSize: 14,
          opacity: loading ? 0.6 : 1,
        }}
      >
        {loading ? "Starting..." : "Excavate"}
      </button>
      {error && <p style={{ color: "var(--rust)" }}>{error}</p>}
    </form>
  );
}
