import { Memory } from "../api/client";

interface MemoryListProps {
  memories: Memory[];
  loading: boolean;
  error: string | null;
  onDelete: (id: string) => Promise<boolean>;
  onEdit: (memory: Memory) => void;
}

export default function MemoryList({
  memories,
  loading,
  error,
  onDelete,
  onEdit,
}: MemoryListProps) {
  if (loading) {
    return <div className="state loading">Loading memories...</div>;
  }

  if (error) {
    return <div className="state error">Error: {error}</div>;
  }

  if (memories.length === 0) {
    return (
      <div className="state empty">
        No memories yet. Create your first memory to get started.
      </div>
    );
  }

  return (
    <div className="memory-list">
      {memories.map((mem) => (
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
            <div className="memory-actions">
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => onEdit(mem)}
              >
                Edit
              </button>
              <button
                className="btn btn-sm btn-danger"
                onClick={() => onDelete(mem.id)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}