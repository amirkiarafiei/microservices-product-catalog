"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check, ChevronsUpDown, Search } from "lucide-react";
import { cn } from "@/lib/utils";

interface Option {
  value: string;
  label: string;
}

interface MultiSelectProps {
  options: Option[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
}

export default function MultiSelect({
  options,
  selected,
  onChange,
  placeholder = "Select options...",
  disabled = false,
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredOptions = options.filter((option) =>
    option.label.toLowerCase().includes(query.toLowerCase())
  );

  const toggleOption = (value: string) => {
    const newSelected = selected.includes(value)
      ? selected.filter((v) => v !== value)
      : [...selected, value];
    onChange(newSelected);
  };

  const removeSelected = (e: React.MouseEvent, value: string) => {
    e.stopPropagation();
    onChange(selected.filter((v) => v !== value));
  };

  return (
    <div ref={containerRef} className="relative w-full">
      <div
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={cn(
          "min-h-[44px] w-full bg-white border rounded-xl px-3 py-1.5 flex flex-wrap gap-2 cursor-pointer transition-all",
          isOpen ? "border-orange-brand ring-4 ring-orange-brand/10" : "border-slate-200",
          disabled && "bg-slate-50 cursor-not-allowed opacity-70"
        )}
      >
        <AnimatePresence>
          {selected.length > 0 ? (
            selected.map((val) => {
              const option = options.find((o) => o.value === val);
              return (
                <motion.span
                  key={val}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="inline-flex items-center bg-orange-light text-orange-brand px-2 py-0.5 rounded-md text-xs font-semibold border border-orange-brand/20"
                >
                  {option?.label || val}
                  <X
                    className="w-3 h-3 ml-1.5 cursor-pointer hover:text-orange-hover"
                    onClick={(e) => removeSelected(e, val)}
                  />
                </motion.span>
              );
            })
          ) : (
            <span className="text-slate-400 text-sm mt-1">{placeholder}</span>
          )}
        </AnimatePresence>
        <div className="flex-grow" />
        <ChevronsUpDown className="w-4 h-4 text-slate-400 self-center" />
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute z-50 w-full mt-2 bg-white border border-slate-100 rounded-xl shadow-2xl overflow-hidden"
          >
            <div className="p-2 border-b border-slate-50">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  autoFocus
                  className="w-full pl-9 pr-4 py-2 text-sm outline-none bg-slate-50/50 rounded-lg"
                  placeholder="Search items..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            </div>
            <div className="max-h-60 overflow-y-auto p-1">
              {filteredOptions.length > 0 ? (
                filteredOptions.map((option) => (
                  <div
                    key={option.value}
                    onClick={() => toggleOption(option.value)}
                    className={cn(
                      "flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors text-sm",
                      selected.includes(option.value)
                        ? "bg-orange-light text-orange-brand"
                        : "hover:bg-slate-50 text-slate-700"
                    )}
                  >
                    <span>{option.label}</span>
                    {selected.includes(option.value) && <Check className="w-4 h-4" />}
                  </div>
                ))
              ) : (
                <div className="p-4 text-center text-slate-400 text-sm italic">
                  No items found
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
