const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type RepoStatus = {
  id: number;
  url: string;
  name: string;
  status: "pending" | "analyzing" | "ready" | "failed";
};

export type FunctionOut = {
  qualified_name: string;
  file_path: string;
  start_line: number;
  end_line: number;
  change_count: number;
  bugfix_count: number;
  risk_score: number;
};

export type GraphResponse = {
  nodes: { id: string; file: string; risk: number }[];
  edges: { source: string; target: string }[];
};

export type ImpactResponse = {
  target: string;
  directly_depends_on: string[];
  directly_depended_by: string[];
  transitive_blast_radius: string[];
  blast_radius_size: number;
};

export type HistoryResponse = {
  qualified_name: string;
  commit_count: number;
  bugfix_count: number;
  authors: string[];
  narrative: string;
};

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  ingestRepo: (url: string) =>
    req<RepoStatus>("/repos", { method: "POST", body: JSON.stringify({ url }) }),
  getRepoStatus: (id: number) => req<RepoStatus>(`/repos/${id}`),
  getGraph: (id: number) => req<GraphResponse>(`/repos/${id}/graph`),
  getTopRisk: (id: number, limit = 20) =>
    req<FunctionOut[]>(`/risk/${id}?limit=${limit}`),
  getImpact: (id: number, qualifiedName: string) =>
    req<ImpactResponse>(`/impact/${id}/${encodeURIComponent(qualifiedName)}`),
  getHistory: (id: number, qualifiedName: string) =>
    req<HistoryResponse>(`/history/${id}/${encodeURIComponent(qualifiedName)}`),
};
