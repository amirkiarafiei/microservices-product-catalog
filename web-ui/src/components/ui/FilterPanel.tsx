"use client";

import React, { useState, useEffect } from "react";
import { 
  Search, 
  X, 
  Filter, 
  ChevronDown, 
  ChevronUp, 
  DollarSign, 
  Box, 
  Globe, 
  Store, 
  Users,
  RefreshCcw
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface FilterPanelProps {
  onFilterChange: (filters: FilterState) => void;
  initialFilters?: FilterState;
}

export interface FilterState {
  q: string;
  min_price: string;
  max_price: string;
  channel: string;
  characteristic: string[];
}

export default function FilterPanel({ onFilterChange, initialFilters }: FilterPanelProps) {
  const [filters, setFilters] = useState<FilterState>(initialFilters || {
    q: "",
    min_price: "",
    max_price: "",
    channel: "",
    characteristic: []
  });

  const [isExpanded, setIsExpanded] = useState(true);

  // Debounce filter changes
  useEffect(() => {
    const handler = setTimeout(() => {
      onFilterChange(filters);
    }, 300);

    return () => clearTimeout(handler);
  }, [filters, onFilterChange]);

  const updateFilter = (key: keyof FilterState, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      q: "",
      min_price: "",
      max_price: "",
      channel: "",
      characteristic: []
    });
  };

  const channels = [
    { id: "Online", icon: Globe },
    { id: "Retail", icon: Store },
    { id: "Partner", icon: Users },
  ];

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden sticky top-8">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 bg-orange-light rounded-lg flex items-center justify-center">
            <Filter className="w-4 h-4 text-orange-brand" />
          </div>
          <h2 className="font-bold text-slate-900 tracking-tight">Filters</h2>
        </div>
        <button 
          onClick={clearFilters}
          className="text-xs font-bold text-slate-400 hover:text-orange-brand flex items-center space-x-1 transition-colors"
        >
          <RefreshCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      <div className="p-6 space-y-8">
        {/* Search */}
        <div className="space-y-3">
          <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Keyword</label>
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-orange-brand transition-colors" />
            <input 
              type="text"
              value={filters.q}
              onChange={(e) => updateFilter("q", e.target.value)}
              placeholder="Search offerings..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all text-sm font-medium"
            />
          </div>
        </div>

        {/* Price Range */}
        <div className="space-y-3">
          <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Price Range</label>
          <div className="grid grid-cols-2 gap-3">
            <div className="relative group">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">$</span>
              <input 
                type="number"
                value={filters.min_price}
                onChange={(e) => updateFilter("min_price", e.target.value)}
                placeholder="Min"
                className="w-full pl-7 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all text-sm font-bold"
              />
            </div>
            <div className="relative group">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">$</span>
              <input 
                type="number"
                value={filters.max_price}
                onChange={(e) => updateFilter("max_price", e.target.value)}
                placeholder="Max"
                className="w-full pl-7 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all text-sm font-bold"
              />
            </div>
          </div>
        </div>

        {/* Sales Channels */}
        <div className="space-y-3">
          <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Sales Channel</label>
          <div className="space-y-2">
            {channels.map((channel) => {
              const isActive = filters.channel === channel.id;
              return (
                <button
                  key={channel.id}
                  onClick={() => updateFilter("channel", isActive ? "" : channel.id)}
                  className={`w-full flex items-center justify-between p-3 rounded-xl border transition-all ${
                    isActive 
                      ? "bg-orange-light border-orange-brand text-orange-brand shadow-sm" 
                      : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <channel.icon className={`w-4 h-4 ${isActive ? "text-orange-brand" : "text-slate-400"}`} />
                    <span className="text-sm font-bold">{channel.id}</span>
                  </div>
                  {isActive && <div className="w-1.5 h-1.5 bg-orange-brand rounded-full shadow-lg shadow-orange-brand/50" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Info Box */}
        <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
          <p className="text-[10px] text-slate-400 leading-relaxed font-medium">
            Search is powered by Elasticsearch. Results are updated in real-time as you type.
          </p>
        </div>
      </div>
    </div>
  );
}
