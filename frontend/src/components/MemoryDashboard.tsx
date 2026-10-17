import { useEffect, useState } from "react";
import { Memory, MemoryCreate, MemoryUpdate } from "../api/client";
import { useMemories } from "../hooks/useMemories";
import MemoryList from "./MemoryList";
import MemoryForm from "./MemoryForm";

export default function MemoryDashboard() {
  const {
    memories,
    loading,
    error,
    total,
    page,
    perPage,
    totalPages,
    fetchPage,
    createMemory,
    updateMemory,
    deleteMemory,
  } = useMemories();

  const [editing, setEditing] = useState<Memory | null>(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchPage(1, perPage);
  }, [fetchPage, perPage]);

  const handleCreate = async (data: MemoryCreate): Promise<Memory | null> => {
    const created = await createMemory(data);
    if (created) {
      setShowForm(false);
      fetchPage(1, perPage);
    }
    return created;
  };

  const handleUpdate = async (
    id: string,
    data: MemoryUpdate,
  ): Promise<Memory | null> => {
    const updated = await updateMemory(id, data);
    if (updated) {
      setEditing(null);
      fetchPage(page, perPage);
    }
    return updated;
  };

  const handleDelete = async (id: string): Promise<boolean> => {
    const ok = await deleteMemory(id);
    if (ok) {
      fetchPage(page, perPage);
    }
    return ok;
  };

  const handleEdit = (memory: Memory) => {
    setEditing(memory);
    setShowForm(true);
  };

  return (
    <div className="memory-dashboard">
      <div className="dashboard-header">
        <h1>Memories</h1>
        <p className="subtitle">
          {total} memories stored • Page {page} of {totalPages || 1}
        </p>
      </div>

      {!showForm && (
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(true)}
        >
          + Create Memory
        </button>
      )}

      {showForm && (
        <div className="form-section">
          <h2>{editing ? "Edit Memory" : "Create Memory"}</h2>
          <MemoryForm
            onSubmit={handleCreate}
            onUpdate={handleUpdate}
            editing={editing}
            onCancelEdit={() => {
              setShowForm(false);
              setEditing(null);
            }}
          />
        </div>
      )}

      <MemoryList
        memories={memories}
        loading={loading}
        error={error}
        onDelete={handleDelete}
        onEdit={handleEdit}
      />

      {totalPages > 1 && (
        <div className="pagination">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(
            (p) => (
              <button
                key={p}
                className={`btn btn-sm ${p === page ? "btn-primary" : "btn-secondary"}`}
                onClick={() => fetchPage(p, perPage)}
              >
                {p}
              </button>
            ),
          )}
        </div>
      )}
    </div>
  );
}