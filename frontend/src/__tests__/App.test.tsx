import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../App";

// Mock the API client with hoisted variables for vi.mock compatibility
const { mockHealth, mockList, mockRankingStats, mockExport } = vi.hoisted(() => ({
  mockHealth: vi.fn().mockResolvedValue({ status: "ok", version: "1.0.0" }),
  mockList: vi.fn().mockResolvedValue({
    items: [], total: 0, page: 1, per_page: 20, pages: 0,
  }),
  mockRankingStats: vi.fn().mockResolvedValue({
    document_count: 0, vocabulary_size: 0, is_indexed: true,
  }),
  mockExport: vi.fn().mockResolvedValue({
    meta: {
      schema_version: "1.0.0",
      source_agent_vendor: "claude",
      destination_agent_vendor: "codex",
      exported_at: "2025-01-01T00:00:00Z",
      exported_by: "nexus-station",
      memory_count: 0,
      filters: {},
    },
    memories: [],
  }),
}));

vi.mock("../api/client.ts", () => ({
  apiClient: {
    health: mockHealth,
    listMemories: mockList,
    createMemory: vi.fn(),
    updateMemory: vi.fn(),
    deleteMemory: vi.fn(),
    getMemory: vi.fn(),
    search: vi.fn(),
    rankingStats: mockRankingStats,
    exportBundle: mockExport,
    importBundle: vi.fn(),
  },
}));

// Mock localStorage for the API client
Object.defineProperty(window, "localStorage", {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
  writable: true,
});

describe("App", () => {
  it("renders navigation links", async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByText("Nexus Station")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Memories/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Search/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Handoff/ })).toBeInTheDocument();
  });

  it("shows health status when API is reachable", async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText(/v1\.0\.0/)).toBeInTheDocument();
    });
  });

  it("renders MemoryDashboard on default route", async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText("+ Create Memory")).toBeInTheDocument();
    });
  });
});