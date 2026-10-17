/**
 * Typed API client for Nexus Station.
 * Derived from the backend routes in backend/app/api/.
 *
 * Base URL: configurable via VITE_API_URL (default: http://localhost:8000)
 * Auth: Bearer token via localStorage (demo mode only).
 */

export interface Memory {
  id: string;
  title: string;
  content: string;
  tags: string[];
  agent_vendor: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryPage {
  items: Memory[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface MemoryCreate {
  title: string;
  content: string;
  tags?: string[];
  agent_vendor: string;
}

export interface MemoryUpdate {
  title?: string;
  content?: string;
  tags?: string[];
  agent_vendor?: string;
}

export interface Bundle {
  meta: {
    schema_version: string;
    source_agent_vendor: string;
    destination_agent_vendor: string;
    exported_at: string;
    exported_by: string;
    memory_count: number;
    filters: Record<string, string | string[]>;
  };
  memories: MemoryCreate[];
}

export interface BundleImportResult {
  bundle_id: string;
  imported_count: number;
  skipped_count: number;
  replaced_count: number;
  conflicts: string[];
}

export interface RankingStats {
  document_count: number;
  vocabulary_size: number;
  is_indexed: boolean;
}

export interface HealthCheck {
  status: string;
  version: string;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_URL}${path}`;
  const headers = new Headers(options.headers);
  const token = localStorage.getItem("nexus_api_key");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  headers.set("Content-Type", "application/json");

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`HTTP ${response.status}: ${detail}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  // Health
  health: () => request<HealthCheck>("/api/v1/healthz"),

  // Memories
  createMemory: (data: MemoryCreate) =>
    request<Memory>("/api/v1/memories", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listMemories: (params: {
    page?: number;
    per_page?: number;
    agent_vendor?: string;
    tag?: string;
  } = {}) => {
    const qs = new URLSearchParams();
    if (params.page) qs.set("page", String(params.page));
    if (params.per_page) qs.set("per_page", String(params.per_page));
    if (params.agent_vendor) qs.set("agent_vendor", params.agent_vendor);
    if (params.tag) qs.set("tag", params.tag);
    const query = qs.toString() ? `?${qs.toString()}` : "";
    return request<MemoryPage>(`/api/v1/memories${query}`);
  },

  getMemory: (id: string) =>
    request<Memory>(`/api/v1/memories/${id}`),

  updateMemory: (id: string, data: MemoryUpdate) =>
    request<Memory>(`/api/v1/memories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteMemory: (id: string) =>
    request<void>(`/api/v1/memories/${id}`, {
      method: "DELETE",
    }),

  // Search
  search: (q: string, params: {
    limit?: number;
    agent_vendor?: string;
    tag?: string;
  } = {}) => {
    const qs = new URLSearchParams();
    qs.set("q", q);
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.agent_vendor) qs.set("agent_vendor", params.agent_vendor);
    if (params.tag) qs.set("tag", params.tag);
    return request<MemoryPage>(`/api/v1/search?${qs.toString()}`);
  },

  rankingStats: () =>
    request<RankingStats>("/api/v1/search/stats"),

  // Handoff
  exportBundle: (req: {
    source_agent_vendor: string;
    destination_agent_vendor: string;
    memory_ids?: string[];
    filters?: Record<string, string | string[]>;
  }) =>
    request<Bundle>("/api/v1/handoff/export", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  importBundle: (bundle: Bundle, opts: {
    bundle_id?: string;
    conflict_resolution?: "new" | "skip" | "replace";
  } = {}) =>
    request<BundleImportResult>("/api/v1/handoff/import", {
      method: "POST",
      body: JSON.stringify({
        bundle,
        bundle_id: opts.bundle_id || "ui-import",
        conflict_resolution: opts.conflict_resolution || "new",
      }),
    }),
};