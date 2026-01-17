"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import { motion } from "framer-motion";
import { LayoutDashboard } from "lucide-react";

export default function BuilderPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8"
        >
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-12 h-12 bg-orange-light rounded-xl flex items-center justify-center">
              <LayoutDashboard className="text-orange-brand w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Builder</h1>
              <p className="text-slate-500">Create and configure catalog entities</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {["Characteristic", "Specification", "Pricing", "Offering"].map((type, i) => (
              <motion.div
                key={type}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                className="group p-6 bg-slate-50 rounded-xl border border-slate-100 hover:border-orange-brand/30 hover:bg-orange-light/30 transition-all cursor-pointer"
              >
                <h3 className="font-semibold text-slate-800 group-hover:text-orange-brand transition-colors">
                  {type}
                </h3>
                <p className="text-sm text-slate-500 mt-1">Configure {type.toLowerCase()} details</p>
              </motion.div>
            ))}
          </div>

          <div className="mt-12 p-24 border-2 border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center text-slate-400">
             <p className="text-lg font-medium">Coming Soon</p>
             <p className="text-sm mt-1">Entity forms will be implemented in the next phase</p>
          </div>
        </motion.div>
      </div>
    </ProtectedRoute>
  );
}
