import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PricingForm from "@/components/forms/PricingForm";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";
import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
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

describe("PricingForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders form fields with default values", () => {
    render(<PricingForm />);
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/price value/i)).toHaveValue(0);
    expect(screen.getByLabelText(/currency/i)).toHaveValue("USD");
  });

  it("submits valid data", async () => {
    const user = userEvent.setup();
    render(<PricingForm />);

    const nameInput = screen.getByLabelText(/name/i);
    await user.clear(nameInput);
    await user.type(nameInput, "Standard Price");
    
    const valueInput = screen.getByLabelText(/price value/i);
    await user.clear(valueInput);
    await user.type(valueInput, "29.99");
    
    const unitInput = screen.getByLabelText(/unit/i);
    await user.clear(unitInput);
    await user.type(unitInput, "per month");
    
    await user.selectOptions(screen.getByLabelText(/currency/i), "EUR");

    await user.click(screen.getByRole("button", { name: /create pricing plan/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith("/prices", {
        name: "Standard Price",
        value: 29.99,
        unit: "per month",
        currency: "EUR"
      });
      expect(toast.success).toHaveBeenCalledWith("Pricing plan created successfully!");
    });
  });

  it("validates positive price", async () => {
    const user = userEvent.setup();
    render(<PricingForm />);

    await user.type(screen.getByLabelText(/name/i), "Bad Price");
    await user.clear(screen.getByLabelText(/price value/i));
    await user.type(screen.getByLabelText(/price value/i), "-5");

    await user.click(screen.getByRole("button", { name: /create pricing plan/i }));

    await waitFor(() => {
      expect(screen.getByText(/price must be positive/i)).toBeInTheDocument();
    });
  });
});
