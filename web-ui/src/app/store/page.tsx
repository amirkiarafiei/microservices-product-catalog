"use client";

import { motion } from "framer-motion";
import { ShoppingBag, Search, Filter } from "lucide-react";

export default function StorePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 space-y-4 md:space-y-0">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-orange-light rounded-xl flex items-center justify-center">
            <ShoppingBag className="text-orange-brand w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Marketplace</h1>
            <p className="text-slate-500">Browse our published product offerings</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search offerings..." 
              className="pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-orange-brand/20 focus:border-orange-brand outline-none transition-all w-full md:w-64"
            />
          </div>
          <button className="p-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
            <Filter className="w-5 h-5 text-slate-600" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {[1, 2, 3, 4, 5, 6].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="group bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="aspect-video bg-slate-100 flex items-center justify-center group-hover:bg-orange-light/50 transition-colors">
              <ShoppingBag className="w-12 h-12 text-slate-300 group-hover:text-orange-brand transition-colors" />
            </div>
            <div className="p-6">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-bold text-slate-900 group-hover:text-orange-brand transition-colors">
                  Product Offering {i+1}
                </h3>
                <span className="text-orange-brand font-bold">$29.99</span>
              </div>
              <p className="text-sm text-slate-500 line-clamp-2">
                This is a sample product offering description that demonstrates the layout of the marketplace grid.
              </p>
              <div className="mt-4 pt-4 border-t border-slate-50 flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Unlimited Data
                </span>
                <button className="text-sm font-semibold text-orange-brand hover:underline">
                  View Details
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
      
      <div className="mt-12 text-center">
        <p className="text-sm text-slate-400">Marketplace items will be fetched from the Store Query Service in the next phase</p>
      </div>
    </div>
  );
}
