import { useState, useEffect } from "react";
import { Bundle, BundleImportResult, Memory } from "../api/client";
import { apiClient } from "../api/client";
import { useMemories } from "../hooks/useMemories";

export default function HandoffPage() {
  const [sourceVendor, setSourceVendor] = useState("claude-code");
  const [destVendor, setDestVendor] = useState("codex");
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [importResult, setImportResult] = useState<BundleImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { memories, fetchPage, refetch } = useMemories();

  useEffect(() => {
    fetchPage(1, 100);
  }, [fetchPage]);

  const handleExportAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const b = await apiClient.exportBundle({
        source_agent_vendor: sourceVendor,
        destination_agent_vendor: destVendor,
      });
      setBundle(b);
      setImportResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setLoading(false);
    }
  };

  const handleExportSelected = async () => {
    const selectedIds = memories
      .filter((m) => m.tags.includes("handoff"))
      .map((m) => m.id);
    if (selectedIds.length === 0) {
      setError("No memories tagged 'handoff' found. Add the 'handoff' tag to memories you want to export.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const b = await apiClient.exportBundle({
        source_agent_vendor: sourceVendor,
        destination_agent_vendor: destVendor,
        memory_ids: selectedIds,
      });
      setBundle(b);
      setImportResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!bundle) {
      setError("No bundle to import. Export first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.importBundle(bundle, {
        bundle_id: `handoff-${Date.now()}`,
        conflict_resolution: "new",
      });
      setImportResult(result);
      refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFileImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const json = JSON.parse(await file.text());
      setBundle(json as Bundle);
      setImportResult(null);
      setError(null);
    } catch (err) {
      setError("Invalid bundle JSON file");
    }
  };

  return (
    <div className="handoff-page">
      <h1>Agent Handoff</h1>

      <section className="handoff-section">
        <h2>Export Bundle</h2>
        <div className="form-row">
          <div className="form-group">
            <label>Source agent</label>
            <input
              type="text"
              value={sourceVendor}
              onChange={(e) => setSourceVendor(e.target.value)}
              placeholder="e.g. claude-code"
            />
          </div>
          <div className="form-group">
            <label>Destination agent</label>
            <input
              type="text"
              value={destVendor}
              onChange={(e) => setDestVendor(e.target.value)}
              placeholder="e.g. codex"
            />
          </div>
        </div>
        <div className="button-group">
          <button className="btn btn-primary" onClick={handleExportAll} disabled={loading}>
            {loading ? "Exporting..." : "Export All Memories"}
          </button>
          <button className="btn btn-secondary" onClick={handleExportSelected} disabled={loading}>
            Export Tagged (handoff)
          </button>
          <label className="btn btn-secondary">
            Import from file...
            <input
              type="file"
              accept=".json,application/json"
              onChange={handleFileImport}
              style={{ display: "none" }}
            />
          </label>
        </div>
      </section>

      {error && <div className="state error">{error}</div>}

      {bundle && (
        <section className="handoff-section">
          <h2>Bundle Preview</h2>
          <p>
            Source: {bundle.meta.source_agent_vendor} → Destination:{" "}
            {bundle.meta.destination_agent_vendor}
          </p>
          <p>Memories: {bundle.meta.memory_count} • Exported: {bundle.meta.exported_at}</p>
          <pre className="bundle-json">
            {JSON.stringify(bundle, null, 2).slice(0, 500)}...
          </pre>
          <button className="btn btn-primary" onClick={handleImport} disabled={loading}>
            {loading ? "Importing..." : "Import Bundle"}
          </button>
        </section>
      )}

      {importResult && (
        <section className="handoff-section">
          <h2>Import Results</h2>
          <p>
            Imported: {importResult.imported_count} •
            Skipped: {importResult.skipped_count} •
            Replaced: {importResult.replaced_count}
          </p>
        </section>
      )}
    </div>
  );
}