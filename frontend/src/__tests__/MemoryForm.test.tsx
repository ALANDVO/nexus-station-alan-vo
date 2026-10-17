import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import MemoryForm from "../components/MemoryForm";

describe("MemoryForm", () => {
  it("renders empty form in create mode", () => {
    render(
      <MemoryForm
        onSubmit={() => Promise.resolve(null)}
        onUpdate={() => Promise.resolve(null)}
      />,
    );
    expect(screen.getByText("Create Memory")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. Fix auth bug in login flow")).toBeInTheDocument();
  });

  it("renders in edit mode with pre-filled values", () => {
    const existing = {
      id: "abc123",
      title: "Existing Title",
      content: "Existing content",
      tags: ["tag1", "tag2"],
      agent_vendor: "claude-code",
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    };
    render(
      <MemoryForm
        onSubmit={() => Promise.resolve(null)}
        onUpdate={() => Promise.resolve(null)}
        editing={existing}
        onCancelEdit={() => {}}
      />,
    );
    expect(screen.getByText("Update Memory")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Existing Title")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Existing content")).toBeInTheDocument();
    expect(screen.getByDisplayValue("claude-code")).toBeInTheDocument();
  });

  it("submits form data and calls onSubmit", async () => {
    const mockSubmit = vi.fn().mockResolvedValue({ id: "new" });
    render(
      <MemoryForm
        onSubmit={mockSubmit}
        onUpdate={() => Promise.resolve(null)}
      />,
    );

    await fireEvent.change(screen.getByPlaceholderText("e.g. Fix auth bug in login flow"), {
      target: { value: "New memory title" },
    });
    await fireEvent.change(screen.getByPlaceholderText("Agent session context, decisions, code snippets..."), {
      target: { value: "Memory content here" },
    });
    await fireEvent.change(screen.getByPlaceholderText("e.g. claude-code"), {
      target: { value: "codex" },
    });
    await fireEvent.change(screen.getByPlaceholderText("e.g. auth, bugfix, important"), {
      target: { value: "auth, bugfix" },
    });

    await fireEvent.click(screen.getByText("Create Memory"));

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        title: "New memory title",
        content: "Memory content here",
        tags: ["auth", "bugfix"],
        agent_vendor: "codex",
      });
    });
  });
});