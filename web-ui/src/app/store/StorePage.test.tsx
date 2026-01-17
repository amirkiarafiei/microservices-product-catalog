import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import StorePage from "@/app/store/page";
import { apiClient } from "@/lib/api-client";
import { vi, describe, it, expect, beforeEach } from "vitest";

// Mock Next.js navigation
const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
  useSearchParams: () => ({
    get: vi.fn(),
    getAll: vi.fn(() => []),
  }),
  usePathname: () => "/store",
}));

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

// Mock simple components to avoid complex interactions
vi.mock("@/components/ui/OfferingCard", () => ({
  default: ({ offering, onClick }: any) => (
    <div data-testid="offering-card" onClick={onClick}>
      {offering.name}
    </div>
  ),
}));

// We can let FilterPanel render if we verify it calls onFilterChange
// But mocking it gives us more control over the filter update triggering
vi.mock("@/components/ui/FilterPanel", () => ({
  default: ({ onFilterChange }: any) => (
    <div>
      <input 
        placeholder="Search..." 
        data-testid="search-input"
        onChange={(e) => onFilterChange({ q: e.target.value, characteristic: [] })} 
      />
    </div>
  ),
}));

describe("StorePage", () => {
  const mockOfferings = {
    total: 2,
    items: [
      { id: "1", name: "Product A", price: 10 },
      { id: "2", name: "Product B", price: 20 },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.get as any).mockResolvedValue(mockOfferings);
  });

  it("renders offerings from API", async () => {
    render(<StorePage />);
    
    // Initially loading
    expect(screen.getByText(/updating.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Product A")).toBeInTheDocument();
      expect(screen.getByText("Product B")).toBeInTheDocument();
    });
    
    expect(screen.getByText(/showing 2 of 2 results/i)).toBeInTheDocument();
  });

  it("updates URL and fetches new data on filter change", async () => {
    const user = userEvent.setup();
    render(<StorePage />);
    await waitFor(() => screen.getByText("Product A"));

    const searchInput = screen.getByTestId("search-input");
    await user.type(searchInput, "Fiber");

    await waitFor(() => {
      // Check if URL update called
      expect(mockReplace).toHaveBeenCalledWith(expect.stringContaining("q=Fiber"), expect.anything());
      // Check if API called with new params
      expect(apiClient.get).toHaveBeenCalledWith("/store/search", expect.objectContaining({
        params: expect.objectContaining({ q: "Fiber" })
      }));
    });
  });

  it("handles API errors gracefully", async () => {
    (apiClient.get as any).mockRejectedValue(new Error("Network Error"));
    render(<StorePage />);

    await waitFor(() => {
      expect(screen.getByText(/oops! something went wrong/i)).toBeInTheDocument();
    });
  });
});
