import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import OfferingForm from "@/components/forms/OfferingForm";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";
import { vi, describe, it, expect, beforeEach } from "vitest";

// Mock dependencies
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock("@/lib/hooks", () => ({
  useSagaPolling: () => ({
    pollStatus: vi.fn(({ onSuccess }) => {
      // Simulate immediate success for testing
      if (onSuccess) onSuccess();
    }),
    isPolling: false,
    pollStatusRef: { current: null },
  }),
}));

vi.mock("react-hot-toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(() => "loading-id"),
  },
}));

// Mock MultiSelect to simplify interaction
vi.mock("@/components/ui/MultiSelect", () => ({
  default: ({ options, selected, onChange, placeholder }: any) => (
    <div data-testid="multiselect">
      <button type="button" onClick={() => onChange([])}>Clear</button>
      {options.map((opt: any) => (
        <button 
          key={opt.value} 
          type="button" 
          onClick={() => {
            const newSelected = selected.includes(opt.value) 
              ? selected.filter((s: string) => s !== opt.value) 
              : [...selected, opt.value];
            onChange(newSelected);
          }}
          data-selected={selected.includes(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  ),
}));

describe("OfferingForm", () => {
  const mockSpecs = [
    { id: "s1", name: "Spec 1" },
    { id: "s2", name: "Spec 2" },
  ];
  const mockPrices = [
    { id: "p1", name: "Price 1" },
    { id: "p2", name: "Price 2" },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.get as any).mockResolvedValueOnce(mockSpecs).mockResolvedValueOnce(mockPrices);
  });

  it("renders form fields and loads dependencies", async () => {
    render(<OfferingForm />);
    
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    
    // Wait for dependencies to load
    await waitFor(() => {
      expect(screen.getByText("Spec 1")).toBeInTheDocument();
      expect(screen.getByText("Price 1")).toBeInTheDocument();
    });
  });

  it("saves draft successfully", async () => {
    const user = userEvent.setup();
    render(<OfferingForm />);

    // Wait for load
    await waitFor(() => screen.getByText("Spec 1"));

    const nameInput = screen.getByLabelText(/name/i);
    await user.clear(nameInput);
    await user.type(nameInput, "Draft Offering");
    await user.click(screen.getByRole("button", { name: /save draft/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith("/offerings", expect.objectContaining({
        name: "Draft Offering",
      }));
      expect(toast.success).toHaveBeenCalledWith("Offering draft saved!");
    });
  });

  it("validates publish requirements", async () => {
    const user = userEvent.setup();
    render(<OfferingForm />);
    await waitFor(() => screen.getByText("Spec 1"));

    // Fill name only
    const nameInput = screen.getByLabelText(/name/i);
    await user.clear(nameInput);
    await user.type(nameInput, "Incomplete Offering");
    
    // Try publish
    await user.click(screen.getByRole("button", { name: /publish now/i }));

    // Should error because no spec/price/channel selected
    expect(toast.error).toHaveBeenCalledWith(expect.stringContaining("Cannot publish"));
  });

  it("publishes successfully when valid", async () => {
    const user = userEvent.setup();
    (apiClient.post as any).mockResolvedValueOnce({ id: "off-1" }).mockResolvedValueOnce({}); // create response, then publish response

    render(<OfferingForm />);
    await waitFor(() => screen.getByText("Spec 1"));

    // Fill all fields
    const nameInput = screen.getByLabelText(/name/i);
    await user.clear(nameInput);
    await user.type(nameInput, "Complete Offering");
    
    // Select spec via mock
    await user.click(screen.getByText("Spec 1"));
    // Select price via mock
    await user.click(screen.getByText("Price 1"));
    
    // NOTE: 'Online' is selected by default in defaultValues. 
    // Toggling it would remove it and cause validation failure.
    // We'll leave it or select another one.
    await user.click(screen.getByText("Retail"));

    // Click publish
    const publishBtn = screen.getByRole("button", { name: /publish now/i });
    await user.click(publishBtn);

    await waitFor(() => {
      // 1. Create
      expect(apiClient.post).toHaveBeenCalledWith("/offerings", expect.any(Object));
      // 2. Publish endpoint call
      expect(apiClient.post).toHaveBeenCalledWith("/offerings/off-1/publish");
    });
  });
});
