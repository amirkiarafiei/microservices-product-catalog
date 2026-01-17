import { render, screen, fireEvent } from "@testing-library/react";
import DataTable from "@/components/ui/DataTable";
import { describe, it, expect } from "vitest";

describe("DataTable", () => {
  const data = [
    { id: 1, name: "Item 1", type: "A" },
    { id: 2, name: "Item 2", type: "B" },
    { id: 3, name: "Item 3", type: "A" },
    { id: 4, name: "Item 4", type: "C" },
    { id: 5, name: "Item 5", type: "B" },
  ];

  const columns = [
    { header: "Name", accessor: "name" as const, sortable: true },
    { header: "Type", accessor: "type" as const, sortable: true },
  ];

  it("renders the data correctly", () => {
    render(<DataTable data={data} columns={columns} />);
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 5")).toBeInTheDocument();
  });

  it("filters data based on search input", () => {
    render(<DataTable data={data} columns={columns} />);
    const searchInput = screen.getByPlaceholderText(/search/i);
    
    fireEvent.change(searchInput, { target: { value: "Item 1" } });
    
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.queryByText("Item 2")).not.toBeInTheDocument();
  });

  it("handles pagination correctly", () => {
    // Render with page size 2
    render(<DataTable data={data} columns={columns} pageSize={2} />);
    
    // First page items
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.queryByText("Item 3")).not.toBeInTheDocument();

    // Click next page (button with text "2")
    const page2Btn = screen.getByRole("button", { name: "2" });
    fireEvent.click(page2Btn);

    // Second page items
    expect(screen.getByText("Item 3")).toBeInTheDocument();
    expect(screen.getByText("Item 4")).toBeInTheDocument();
    expect(screen.queryByText("Item 1")).not.toBeInTheDocument();
  });
});
