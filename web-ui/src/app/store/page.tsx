"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { 
  ShoppingBag, 
  Loader2, 
  AlertCircle,
  Plus
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";
import FilterPanel, { FilterState } from "@/components/ui/FilterPanel";
import OfferingCard from "@/components/ui/OfferingCard";
import OfferingDetail from "@/components/ui/OfferingDetail";
import Modal from "@/components/ui/Modal";

function StoreContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  
  const [offerings, setOfferings] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedOffering, setSelectedOffering] = useState<any>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [skip, setSkip] = useState(0);
  const LIMIT = 12;

  // Memoize filters from URL to prevent re-creation on every render
  const initialFilters: FilterState = useMemo(() => ({
    q: searchParams.get("q") || "",
    min_price: searchParams.get("min_price") || "",
    max_price: searchParams.get("max_price") || "",
    channel: searchParams.get("channel") || "",
    characteristic: searchParams.getAll("characteristic") || []
  }), [searchParams]);

  const fetchOfferings = useCallback(async (filters: FilterState, append = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = {
        skip: append ? skip + LIMIT : 0,
        limit: LIMIT
      };
      
      if (filters.q) params.q = filters.q;
      if (filters.min_price) params.min_price = filters.min_price;
      if (filters.max_price) params.max_price = filters.max_price;
      if (filters.channel) params.channel = filters.channel;
      if (filters.characteristic.length > 0) params.characteristic = filters.characteristic;

      const result = await apiClient.get<any>("/store/search", { params });
      
      if (append) {
        setOfferings(prev => [...prev, ...result.items]);
        setSkip(prev => prev + LIMIT);
      } else {
        setOfferings(result.items);
        setSkip(0);
      }
      setTotal(result.total);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load product offerings. Please try again later.");
      toast.error("Could not connect to the store service.");
    } finally {
      setIsLoading(false);
    }
  }, [skip]);

  const handleFilterChange = useCallback((newFilters: FilterState) => {
    // Update URL params
    const params = new URLSearchParams();
    if (newFilters.q) params.set("q", newFilters.q);
    if (newFilters.min_price) params.set("min_price", newFilters.min_price);
    if (newFilters.max_price) params.set("max_price", newFilters.max_price);
    if (newFilters.channel) params.set("channel", newFilters.channel);
    newFilters.characteristic.forEach(c => params.append("characteristic", c));
    
    const query = params.toString();
    router.replace(`${pathname}${query ? `?${query}` : ""}`, { scroll: false });
    
    fetchOfferings(newFilters);
  }, [router, pathname, fetchOfferings]);

  const handleLoadMore = useCallback(() => {
    fetchOfferings(initialFilters, true);
  }, [fetchOfferings, initialFilters]);

  // Fetch offerings on mount and when filters change
  useEffect(() => {
    fetchOfferings(initialFilters);
  }, [fetchOfferings, initialFilters]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
        <div className="flex items-center space-x-4">
          <div className="w-14 h-14 bg-orange-brand rounded-2xl flex items-center justify-center shadow-lg shadow-orange-brand/20">
            <ShoppingBag className="text-white w-7 h-7" />
          </div>
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight">Marketplace</h1>
            <p className="text-slate-500 font-medium mt-1">Discover our latest telecommunication products</p>
          </div>
        </div>
        <div className="bg-slate-100 px-4 py-2 rounded-xl border border-slate-200">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">
            {isLoading ? "Updating..." : `Showing ${offerings?.length || 0} of ${total} results`}
          </span>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-10">
        {/* Sidebar / Filters */}
        <aside className="lg:w-80 flex-shrink-0">
          <FilterPanel 
            onFilterChange={handleFilterChange} 
            initialFilters={initialFilters} 
          />
        </aside>

        {/* Results Grid */}
        <main className="flex-grow">
          {error ? (
            <div className="bg-red-50 border border-red-100 rounded-3xl p-12 text-center flex flex-col items-center space-y-4">
              <AlertCircle className="w-12 h-12 text-red-400" />
              <h3 className="text-xl font-bold text-red-900">Oops! Something went wrong</h3>
              <p className="text-red-600 font-medium max-w-sm mx-auto">{error}</p>
              <button 
                onClick={() => fetchOfferings(initialFilters)}
                className="mt-4 px-6 py-2.5 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 transition-all shadow-lg shadow-red-600/20"
              >
                Try Again
              </button>
            </div>
          ) : (!offerings || offerings.length === 0) && !isLoading ? (
            <div className="bg-slate-50 border border-dashed border-slate-200 rounded-3xl p-20 text-center flex flex-col items-center space-y-4">
              <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-sm mb-2">
                <ShoppingBag className="w-8 h-8 text-slate-200" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">No offerings found</h3>
              <p className="text-slate-500 font-medium max-w-xs mx-auto">Try adjusting your filters or keyword to find what you&apos;re looking for.</p>
            </div>
          ) : (
            <div className="space-y-12">
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                <AnimatePresence mode="popLayout">
                  {offerings?.map((offering) => (
                    <OfferingCard 
                      key={offering.id} 
                      offering={offering} 
                      onClick={() => setSelectedOffering(offering)}
                    />
                  ))}
                </AnimatePresence>
                
                {isLoading && Array.from({ length: 3 }).map((_, i) => (
                  <div key={`skeleton-${i}`} className="bg-slate-100 animate-pulse rounded-3xl h-96 border border-slate-200" />
                ))}
              </div>

              {(offerings?.length || 0) < total && (
                <div className="flex justify-center pt-8 border-t border-slate-100">
                  <button
                    onClick={handleLoadMore}
                    disabled={isLoading}
                    className="flex items-center space-x-2.5 px-8 py-4 bg-white border-2 border-slate-900 text-slate-900 rounded-2xl font-black hover:bg-slate-900 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
                  >
                    {isLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform" />
                        <span>Load More Products</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Detail Modal */}
      <Modal
        isOpen={!!selectedOffering}
        onClose={() => setSelectedOffering(null)}
        title="Product Details"
        size="lg"
      >
        {selectedOffering && (
          <OfferingDetail offering={selectedOffering} />
        )}
      </Modal>
    </div>
  );
}

export default function StorePage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-12 h-12 animate-spin text-orange-brand" />
        <p className="text-slate-400 font-bold tracking-widest uppercase text-[10px]">Entering Marketplace...</p>
      </div>
    }>
      <StoreContent />
    </Suspense>
  );
}
