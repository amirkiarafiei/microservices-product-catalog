import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import FilterPanel from "./FilterPanel";

describe("FilterPanel", () => {
  it("renders all filter sections", () => {
    render(<FilterPanel onFilterChange={() => {}} />);
    
    expect(screen.getByText("Keyword")).toBeDefined();
    expect(screen.getByText("Price Range")).toBeDefined();
    expect(screen.getByText("Sales Channel")).toBeDefined();
    expect(screen.getByPlaceholderText("Search offerings...")).toBeDefined();
  });

  it("calls onFilterChange when keyword is typed (with debounce)", async () => {
    const handleFilterChange = vi.fn();
    render(<FilterPanel onFilterChange={handleFilterChange} />);
    
    const input = screen.getByPlaceholderText("Search offerings...");
    fireEvent.change(input, { target: { value: "fiber" } });
    
    // Should not be called immediately due to debounce
    expect(handleFilterChange).not.toHaveBeenCalled();
    
    // Wait for debounce (300ms)
    await waitFor(() => {
      expect(handleFilterChange).toHaveBeenCalledWith(expect.objectContaining({ q: "fiber" }));
    }, { timeout: 1000 });
  });

  it("updates price filters correctly", async () => {
    const handleFilterChange = vi.fn();
    render(<FilterPanel onFilterChange={handleFilterChange} />);
    
    const minInput = screen.getByPlaceholderText("Min");
    fireEvent.change(minInput, { target: { value: "10" } });
    
    await waitFor(() => {
      expect(handleFilterChange).toHaveBeenCalledWith(expect.objectContaining({ min_price: "10" }));
    });
  });

  it("toggles sales channel filter", async () => {
    const handleFilterChange = vi.fn();
    render(<FilterPanel onFilterChange={handleFilterChange} />);
    
    const onlineBtn = screen.getByText("Online");
    fireEvent.click(onlineBtn);
    
    await waitFor(() => {
      expect(handleFilterChange).toHaveBeenCalledWith(expect.objectContaining({ channel: "Online" }));
    });
    
    // Click again to deselect
    fireEvent.click(onlineBtn);
    
    await waitFor(() => {
      expect(handleFilterChange).toHaveBeenCalledWith(expect.objectContaining({ channel: "" }));
    });
  });

  it("clears all filters when reset is clicked", async () => {
    const handleFilterChange = vi.fn();
    render(<FilterPanel 
      onFilterChange={handleFilterChange} 
      initialFilters={{ q: "fiber", min_price: "10", max_price: "100", channel: "Online", characteristic: [] }} 
    />);
    
    const resetBtn = screen.getByText("Reset");
    fireEvent.click(resetBtn);
    
    await waitFor(() => {
      expect(handleFilterChange).toHaveBeenCalledWith({
        q: "",
        min_price: "",
        max_price: "",
        channel: "",
        characteristic: []
      });
    });
  });
});
