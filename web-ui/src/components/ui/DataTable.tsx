"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ChevronLeft, 
  ChevronRight, 
  ChevronsLeft, 
  ChevronsRight,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface Column<T> {
  header: string;
  accessor: keyof T | ((item: T) => React.ReactNode);
  sortable?: boolean;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  pageSize?: number;
  isLoading?: boolean;
  searchPlaceholder?: string;
  emptyMessage?: string;
}

export default function DataTable<T extends { id: string | number }>({
  data,
  columns,
  pageSize = 10,
  isLoading = false,
  searchPlaceholder = "Search...",
  emptyMessage = "No data available",
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState<{ key: keyof T | null; direction: "asc" | "desc" | null }>({
    key: null,
    direction: null,
  });

  // Filtering
  const filteredData = useMemo(() => {
    return data.filter((item) => {
      return Object.values(item).some((val) =>
        String(val).toLowerCase().includes(searchTerm.toLowerCase())
      );
    });
  }, [data, searchTerm]);

  // Sorting
  const sortedData = useMemo(() => {
    if (!sortConfig.key || !sortConfig.direction) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aVal = a[sortConfig.key!];
      const bVal = b[sortConfig.key!];

      if (aVal < bVal) return sortConfig.direction === "asc" ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === "asc" ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortConfig]);

  // Pagination
  const totalPages = Math.ceil(sortedData.length / pageSize);
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const handleSort = (key: keyof T) => {
    let direction: "asc" | "desc" | null = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    } else if (sortConfig.key === key && sortConfig.direction === "desc") {
      direction = null;
    }
    setSortConfig({ key: direction ? key : null, direction });
  };

  const renderSortIcon = (column: Column<T>) => {
    if (!column.sortable) return null;
    if (sortConfig.key !== column.accessor) return <ArrowUpDown className="w-3 h-3 ml-1 text-slate-300" />;
    return sortConfig.direction === "asc" 
      ? <ArrowUp className="w-3 h-3 ml-1 text-orange-brand" /> 
      : <ArrowDown className="w-3 h-3 ml-1 text-orange-brand" />;
  };

  return (
    <div className="w-full space-y-4">
      {/* Table Header / Search */}
      <div className="flex justify-between items-center px-1">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder={searchPlaceholder}
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all text-sm"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
          />
        </div>
        <div className="text-xs text-slate-400 font-medium">
          Showing {paginatedData.length} of {filteredData.length} entries
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-100">
                {columns.map((col, idx) => (
                  <th
                    key={idx}
                    className={cn(
                      "px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider",
                      col.sortable && "cursor-pointer hover:text-slate-700 transition-colors",
                      col.className
                    )}
                    onClick={() => col.sortable && typeof col.accessor === "string" && handleSort(col.accessor as keyof T)}
                  >
                    <div className="flex items-center">
                      {col.header}
                      {renderSortIcon(col)}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              <AnimatePresence mode="popLayout">
                {isLoading ? (
                  Array.from({ length: pageSize }).map((_, i) => (
                    <tr key={`skeleton-${i}`} className="animate-pulse">
                      {columns.map((_, j) => (
                        <td key={j} className="px-6 py-4">
                          <div className="h-4 bg-slate-100 rounded-md w-3/4" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : paginatedData.length > 0 ? (
                  paginatedData.map((item, idx) => (
                    <motion.tr
                      key={item.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2, delay: idx * 0.03 }}
                      className="group hover:bg-slate-50/50 transition-colors"
                    >
                      {columns.map((col, j) => (
                        <td key={j} className={cn("px-6 py-4 text-sm text-slate-600", col.className)}>
                          {typeof col.accessor === "function" 
                            ? col.accessor(item) 
                            : (item[col.accessor as keyof T] as React.ReactNode)}
                        </td>
                      ))}
                    </motion.tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={columns.length} className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center justify-center space-y-2">
                        <div className="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center">
                          <Search className="w-6 h-6 text-slate-300" />
                        </div>
                        <p className="text-slate-400 text-sm font-medium">{emptyMessage}</p>
                      </div>
                    </td>
                  </tr>
                )}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
              className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronsLeft className="w-4 h-4 text-slate-600" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4 text-slate-600" />
            </button>
          </div>

          <div className="flex items-center space-x-2">
            {Array.from({ length: totalPages }).map((_, i) => {
              const page = i + 1;
              // Simple logic to show current, first, last, and neighbors
              if (
                page === 1 || 
                page === totalPages || 
                (page >= currentPage - 1 && page <= currentPage + 1)
              ) {
                return (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={cn(
                      "w-8 h-8 rounded-lg text-xs font-bold transition-all",
                      currentPage === page 
                        ? "bg-orange-brand text-white shadow-lg shadow-orange-brand/20" 
                        : "text-slate-500 hover:bg-slate-100"
                    )}
                  >
                    {page}
                  </button>
                );
              } else if (page === currentPage - 2 || page === currentPage + 2) {
                return <span key={page} className="text-slate-300 px-1">...</span>;
              }
              return null;
            })}
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4 text-slate-600" />
            </button>
            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronsRight className="w-4 h-4 text-slate-600" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
