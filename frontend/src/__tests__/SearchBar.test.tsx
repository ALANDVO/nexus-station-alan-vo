import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SearchBar from "../components/SearchBar";

describe("SearchBar", () => {
  it("renders with search input and stats", () => {
    const stats = {
      document_count: 42,
      vocabulary_size: 100,
      is_indexed: true,
    };
    render(
      <SearchBar
        onSearch={() => Promise.resolve()}
        stats={stats}
        onFetchStats={() => Promise.resolve()}
      />,
    );
    expect(screen.getByPlaceholderText("Enter search terms...")).toBeInTheDocument();
    expect(screen.getByText("Corpus: 42 memories")).toBeInTheDocument();
    expect(screen.getByText("Vocabulary: 100 terms")).toBeInTheDocument();
  });

  it("calls onSearch with query and filters when submitted", async () => {
    const mockSearch = vi.fn().mockResolvedValue(undefined);
    render(
      <SearchBar
        onSearch={mockSearch}
        stats={null}
        onFetchStats={() => Promise.resolve()}
      />,
    );

    await fireEvent.change(screen.getByPlaceholderText("Enter search terms..."), {
      target: { value: "oauth callback" },
    });
    await fireEvent.change(screen.getByPlaceholderText("e.g. claude-code"), {
      target: { value: "claude-code" },
    });

    await fireEvent.click(screen.getByText("Search"));

    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalledWith("oauth callback", {
        agent_vendor: "claude-code",
        tag: undefined,
      });
    });
  });

  it("does not call onSearch with empty query", async () => {
    const mockSearch = vi.fn();
    render(
      <SearchBar
        onSearch={mockSearch}
        stats={null}
        onFetchStats={() => Promise.resolve()}
      />,
    );

    await fireEvent.click(screen.getByText("Search"));
    expect(mockSearch).not.toHaveBeenCalled();
  });
});