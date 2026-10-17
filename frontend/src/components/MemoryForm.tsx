import { useState, useEffect } from "react";
import { Memory, MemoryCreate, MemoryUpdate } from "../api/client";

interface MemoryFormProps {
  onSubmit: (data: MemoryCreate) => Promise<Memory | null>;
  onUpdate: (id: string, data: MemoryUpdate) => Promise<Memory | null>;
  editing?: Memory | null;
  onCancelEdit?: () => void;
}

export default function MemoryForm({
  onSubmit,
  onUpdate,
  editing,
  onCancelEdit,
}: MemoryFormProps) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const [agentVendor, setAgentVendor] = useState("");

  useEffect(() => {
    if (editing) {
      setTitle(editing.title);
      setContent(editing.content);
      setTags(editing.tags.join(", "));
      setAgentVendor(editing.agent_vendor);
    }
  }, [editing]);

  const resetForm = () => {
    setTitle("");
    setContent("");
    setTags("");
    setAgentVendor("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const tagList = tags
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    if (editing) {
      const result = await onUpdate(editing.id, {
        title,
        content,
        tags: tagList,
        agent_vendor: agentVendor,
      });
      if (result) {
        resetForm();
        onCancelEdit?.();
      }
    } else {
      const result = await onSubmit({
        title,
        content,
        tags: tagList,
        agent_vendor: agentVendor,
      });
      if (result) {
        resetForm();
      }
    }
  };

  return (
    <form className="memory-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="title">Title</label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Fix auth bug in login flow"
          required
          maxLength={200}
        />
      </div>
      <div className="form-group">
        <label htmlFor="content">Content</label>
        <textarea
          id="content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Agent session context, decisions, code snippets..."
          required
          rows={4}
        />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="agent_vendor">Agent Vendor</label>
          <input
            id="agent_vendor"
            type="text"
            value={agentVendor}
            onChange={(e) => setAgentVendor(e.target.value)}
            placeholder="e.g. claude-code"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="tags">Tags (comma-separated)</label>
          <input
            id="tags"
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="e.g. auth, bugfix, important"
          />
        </div>
      </div>
      <button type="submit" className="btn btn-primary">
        {editing ? "Update Memory" : "Create Memory"}
      </button>
      {editing && onCancelEdit && (
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onCancelEdit}
        >
          Cancel
        </button>
      )}
    </form>
  );
}