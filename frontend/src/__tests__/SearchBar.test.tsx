import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SearchBar from "../components/SearchBar";
describe("SearchBar", () => {
  it("renders with search input and stats", () => {
    const stats = {
      document_count: 42,
      vocabulary_size: 100,
      is_indexed: true,
    };
    act(() => {
      render(
        <SearchBar
          onSearch={() => Promise.resolve()}
          stats={stats}
          onFetchStats={() => Promise.resolve()}
        />,
      );
    });
    expect(screen.getByPlaceholderText("Enter search terms...")).toBeInTheDocument();
    expect(screen.getByText("Corpus: 42 memories")).toBeInTheDocument();
    expect(screen.getByText("Vocabulary: 100 terms")).toBeInTheDocument();
  });

  it("calls onSearch with query and filters when submitted", async () => {
    const mockSearch = vi.fn().mockResolvedValue(undefined);
    act(() => {
      render(
        <SearchBar
          onSearch={mockSearch}
          stats={null}
          onFetchStats={() => Promise.resolve()}
        />,
      );
    });

    const user = userEvent.setup();
    await user.type(screen.getByPlaceholderText("Enter search terms..."), "oauth callback");
    await user.type(screen.getByPlaceholderText("e.g. claude-code"), "claude-code");

    await user.click(screen.getByText("Search"));

    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalledWith("oauth callback", {
        agent_vendor: "claude-code",
        tag: undefined,
      });
    });
  });

  it("does not call onSearch with empty query", async () => {
    const mockSearch = vi.fn();
    act(() => {
      render(
        <SearchBar
          onSearch={mockSearch}
          stats={null}
          onFetchStats={() => Promise.resolve()}
        />,
      );
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("Search"));
    expect(mockSearch).not.toHaveBeenCalled();
  });
});