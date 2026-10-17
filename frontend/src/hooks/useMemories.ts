/**
 * Data-fetching hooks for memory operations.
 * Uses the typed API client; all state is local to the hook instance.
 */
import { useState, useCallback } from "react";
import {
  apiClient,
  Memory,
  MemoryCreate,
  MemoryPage,
  MemoryUpdate,
  RankingStats,
} from "../api/client";

export interface UseMemoriesResult {
  memories: Memory[];
  loading: boolean;
  error: string | null;
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
  fetchPage: (page: number, perPage: number) => Promise<void>;
  createMemory: (data: MemoryCreate) => Promise<Memory | null>;
  updateMemory: (id: string, data: MemoryUpdate) => Promise<Memory | null>;
  deleteMemory: (id: string) => Promise<boolean>;
  refetch: () => Promise<void>;
}

export function useMemories(): UseMemoriesResult {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    perPage: 20,
    totalPages: 0,
  });

  const fetchPage = useCallback(
    async (page: number, perPage: number) => {
      setLoading(true);
      setError(null);
      try {
        const data: MemoryPage = await apiClient.listMemories({
          page,
          per_page: perPage,
        });
        setMemories(data.items);
        setPagination({
          total: data.total,
          page: data.page,
          perPage: data.per_page,
          totalPages: data.pages,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch");
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const createMemory = useCallback(
    async (data: MemoryCreate): Promise<Memory | null> => {
      setError(null);
      try {
        const mem = await apiClient.createMemory(data);
        setMemories((prev) => [mem, ...prev]);
        setPagination((p) => ({ ...p, total: p.total + 1 }));
        return mem;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create");
        return null;
      }
    },
    [],
  );

  const updateMemory = useCallback(
    async (id: string, data: MemoryUpdate): Promise<Memory | null> => {
      try {
        const updated = await apiClient.updateMemory(id, data);
        setMemories((prev) =>
          prev.map((m) => (m.id === id ? updated : m)),
        );
        return updated;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to update");
        return null;
      }
    },
    [],
  );

  const deleteMemory = useCallback(
    async (id: string): Promise<boolean> => {
      try {
        await apiClient.deleteMemory(id);
        setMemories((prev) => prev.filter((m) => m.id !== id));
        setPagination((p) => ({ ...p, total: p.total - 1 }));
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete");
        return false;
      }
    },
    [],
  );

  const refetch = useCallback(async () => {
    await fetchPage(pagination.page, pagination.perPage);
  }, [fetchPage, pagination.page, pagination.perPage]);

  return {
    memories,
    loading,
    error,
    total: pagination.total,
    page: pagination.page,
    perPage: pagination.perPage,
    totalPages: pagination.totalPages,
    fetchPage,
    createMemory,
    updateMemory,
    deleteMemory,
    refetch,
  };
}

export interface UseSearchResult {
  results: Memory[];
  loading: boolean;
  error: string | null;
  total: number;
  performSearch: (q: string, filters?: { agent_vendor?: string; tag?: string }) => Promise<void>;
  stats: RankingStats | null;
  fetchStats: () => Promise<void>;
}

export function useSearch(): UseSearchResult {
  const [results, setResults] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<RankingStats | null>(null);

  const performSearch = useCallback(
    async (q: string, filters?: { agent_vendor?: string; tag?: string }) => {
      setLoading(true);
      setError(null);
      try {
        const data: MemoryPage = await apiClient.search(q, {
          limit: 50,
          agent_vendor: filters?.agent_vendor,
          tag: filters?.tag,
        });
        setResults(data.items);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed");
        setResults([]);
        setTotal(0);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const fetchStats = useCallback(async () => {
    try {
      const s = await apiClient.rankingStats();
      setStats(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch stats");
    }
  }, []);

  return { results, loading, error, total, performSearch, stats, fetchStats };
}