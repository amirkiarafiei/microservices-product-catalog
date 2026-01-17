"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import { motion } from "framer-motion";
import { Layers } from "lucide-react";

export default function ViewerPage() {
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
              <Layers className="text-orange-brand w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Viewer</h1>
              <p className="text-slate-500">Browse and manage existing entities</p>
            </div>
          </div>

          <div className="mt-8 overflow-hidden rounded-xl border border-slate-100">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-100">
                <tr>
                  <th className="px-6 py-4 text-sm font-semibold text-slate-900">Name</th>
                  <th className="px-6 py-4 text-sm font-semibold text-slate-900">Type</th>
                  <th className="px-6 py-4 text-sm font-semibold text-slate-900">Status</th>
                  <th className="px-6 py-4 text-sm font-semibold text-slate-900">Created At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[1, 2, 3].map((_, i) => (
                  <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4 text-sm text-slate-600 font-medium">Sample Entity {i+1}</td>
                    <td className="px-6 py-4 text-sm text-slate-500">Characteristic</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider bg-green-100 text-green-700 rounded-md">
                        Active
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">2026-01-17</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="mt-8 flex justify-center">
            <p className="text-sm text-slate-400">Data viewer will be fully connected in the next phase</p>
          </div>
        </motion.div>
      </div>
    </ProtectedRoute>
  );
}
