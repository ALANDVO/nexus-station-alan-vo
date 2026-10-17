import { useState } from "react";
import { RankingStats } from "../api/client";

interface SearchBarProps {
  onSearch: (
    q: string,
    filters?: { agent_vendor?: string; tag?: string },
  ) => Promise<void>;
  stats: RankingStats | null;
  onFetchStats: () => Promise<void>;
}

export default function SearchBar({
  onSearch,
  stats,
  onFetchStats,
}: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [vendorFilter, setVendorFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    await onSearch(query, {
      agent_vendor: vendorFilter || undefined,
      tag: tagFilter || undefined,
    });
    setIsSearching(false);
  };

  return (
    <div className="search-bar">
      <form onSubmit={handleSearch} className="search-form">
        <div className="form-group">
          <label htmlFor="search-query">Search memories (TF-IDF)</label>
          <input
            id="search-query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter search terms..."
            required
            maxLength={500}
          />
        </div>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="vendor-filter">Agent vendor</label>
            <input
              id="vendor-filter"
              type="text"
              value={vendorFilter}
              onChange={(e) => setVendorFilter(e.target.value)}
              placeholder="e.g. claude-code"
            />
          </div>
          <div className="form-group">
            <label htmlFor="tag-filter">Tag filter</label>
            <input
              id="tag-filter"
              type="text"
              value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value)}
              placeholder="e.g. important"
            />
          </div>
        </div>
        <button type="submit" className="btn btn-primary" disabled={isSearching}>
          {isSearching ? "Searching..." : "Search"}
        </button>
      </form>
      {stats && (
        <div className="search-stats">
          <span>Corpus: {stats.document_count} memories</span>
          <span>Vocabulary: {stats.vocabulary_size} terms</span>
        </div>
      )}
    </div>
  );
}