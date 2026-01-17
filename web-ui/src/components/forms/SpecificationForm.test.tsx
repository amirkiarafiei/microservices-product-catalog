import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SpecificationForm from "@/components/forms/SpecificationForm";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";
import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

vi.mock("react-hot-toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock MultiSelect
vi.mock("@/components/ui/MultiSelect", () => ({
  default: ({ options, selected, onChange }: any) => (
    <div data-testid="multiselect">
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
        >
          {opt.label}
        </button>
      ))}
    </div>
  ),
}));

describe("SpecificationForm", () => {
  const mockChars = [
    { id: "c1", name: "Speed", value: "100", unit_of_measure: "Mbps" },
    { id: "c2", name: "Color", value: "Red", unit_of_measure: "None" },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.get as any).mockResolvedValue(mockChars);
  });

  it("renders and loads characteristics", async () => {
    render(<SpecificationForm />);
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Speed/)).toBeInTheDocument();
    });
  });

  it("submits successfully with valid data", async () => {
    const user = userEvent.setup();
    render(<SpecificationForm />);
    await waitFor(() => screen.getByText(/Speed/));

    await user.type(screen.getByLabelText(/name/i), "My Spec");
    await user.click(screen.getByText(/Speed/)); // Select char

    await user.click(screen.getByRole("button", { name: /create specification/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith("/specifications", {
        name: "My Spec",
        characteristic_ids: ["c1"]
      });
      expect(toast.success).toHaveBeenCalledWith("Specification created successfully!");
    });
  });

  it("shows validation error if no characteristic selected", async () => {
    const user = userEvent.setup();
    render(<SpecificationForm />);
    await waitFor(() => screen.getByText(/Speed/));

    await user.type(screen.getByLabelText(/name/i), "Empty Spec");
    await user.click(screen.getByRole("button", { name: /create specification/i }));

    await waitFor(() => {
      expect(screen.getByText(/select at least one characteristic/i)).toBeInTheDocument();
    });
  });
});
