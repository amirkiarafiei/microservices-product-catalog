import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import OfferingCard from "./OfferingCard";

const mockOffering = {
  id: "off-123",
  name: "Fiber Ultra 500",
  description: "High speed fiber internet",
  lifecycle_status: "PUBLISHED",
  sales_channels: ["Online", "Retail"],
  pricing: [
    { id: "p1", name: "Standard", value: 50, currency: "USD", unit: "per month" },
    { id: "p2", name: "Promo", value: 40, currency: "USD", unit: "per month" }
  ],
  specifications: [
    {
      id: "s1",
      name: "Internet Spec",
      characteristics: [
        { id: "c1", name: "Download Speed", value: "500", unit_of_measure: "Mbps" },
        { id: "c2", name: "Upload Speed", value: "200", unit_of_measure: "Mbps" }
      ]
    }
  ]
};

describe("OfferingCard", () => {
  it("renders offering details correctly", () => {
    render(<OfferingCard offering={mockOffering} onClick={() => {}} />);
    
    expect(screen.getByText("Fiber Ultra 500")).toBeDefined();
    expect(screen.getByText("High speed fiber internet")).toBeDefined();
    expect(screen.getByText("PUBLISHED")).toBeDefined();
    
    // Should show the lowest price
    expect(screen.getByText("40")).toBeDefined();
    expect(screen.getByText("USD")).toBeDefined();
    
    // Should show top characteristics
    expect(screen.getByText("Download Speed:")).toBeDefined();
    expect(screen.getByText("500 Mbps")).toBeDefined();
  });

  it("calls onClick when the action button is clicked", () => {
    const handleClick = vi.fn();
    render(<OfferingCard offering={mockOffering} onClick={handleClick} />);
    
    const button = screen.getByRole("button");
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("renders fallback for missing description", () => {
    const minimalOffering = { ...mockOffering, description: undefined };
    render(<OfferingCard offering={minimalOffering} onClick={() => {}} />);
    
    expect(screen.getByText(/Premium product offering/i)).toBeDefined();
  });
});
