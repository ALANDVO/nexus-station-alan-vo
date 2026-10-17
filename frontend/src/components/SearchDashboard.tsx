import { useEffect } from "react";
import { Memory } from "../api/client";
import { useSearch } from "../hooks/useMemories";
import SearchBar from "./SearchBar";

export default function SearchDashboard() {
  const { results, loading, error, total, performSearch, stats, fetchStats } =
    useSearch();

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  if (error && !results.length) {
    return (
      <div className="search-dashboard">
        <SearchBar
          onSearch={performSearch}
          stats={stats}
          onFetchStats={fetchStats}
        />
        <div className="state error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="search-dashboard">
      <SearchBar
        onSearch={performSearch}
        stats={stats}
        onFetchStats={fetchStats}
      />
      {loading && <div className="state loading">Searching memories...</div>}
      {!loading && results.length === 0 && !error && (
        <div className="state empty">
          Enter a search query to find memories by semantic similarity.
        </div>
      )}
      {!loading && results.length > 0 && (
        <div className="search-results">
          <h2>Search Results ({total})</h2>
          <div className="memory-list">
            {results.map((mem: Memory) => (
              <div key={mem.id} className="memory-card">
                <div className="memory-header">
                  <h3 className="memory-title">{mem.title}</h3>
                  <span className="memory-vendor">{mem.agent_vendor}</span>
                </div>
                <p className="memory-content">{mem.content}</p>
                {mem.tags.length > 0 && (
                  <div className="memory-tags">
                    {mem.tags.map((tag) => (
                      <span key={tag} className="memory-tag">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
                <div className="memory-meta">
                  <time className="memory-time">
                    {new Date(mem.created_at).toLocaleString()}
                  </time>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}