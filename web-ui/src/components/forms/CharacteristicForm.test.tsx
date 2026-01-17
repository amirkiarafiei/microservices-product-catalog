import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CharacteristicForm from "@/components/forms/CharacteristicForm";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";
import { vi, describe, it, expect, beforeEach } from "vitest";

describe("CharacteristicForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the form fields", () => {
    render(<CharacteristicForm />);
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/value/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/unit of measure/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create characteristic/i })).toBeInTheDocument();
  });

  it("shows validation errors for empty fields", async () => {
    render(<CharacteristicForm />);
    const submitBtn = screen.getByRole("button", { name: /create characteristic/i });
    
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/value is required/i)).toBeInTheDocument();
    });
  });

  it("submits the form successfully", async () => {
    const user = userEvent.setup();
    (apiClient.post as any).mockResolvedValue({ id: "123" });

    render(<CharacteristicForm />);

    await user.type(screen.getByLabelText(/name/i), "Download Speed");
    await user.type(screen.getByLabelText(/value/i), "500");
    await user.selectOptions(screen.getByLabelText(/unit of measure/i), "Mbps");

    await user.click(screen.getByRole("button", { name: /create characteristic/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith("/characteristics", {
        name: "Download Speed",
        value: "500",
        unit_of_measure: "Mbps",
      });
      expect(toast.success).toHaveBeenCalledWith("Characteristic created successfully!");
    });
  });
});
