"use client";

import React, { useState } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { motion, AnimatePresence } from "framer-motion";
import { LayoutDashboard, Settings2, Box, DollarSign, ShoppingBag } from "lucide-react";
import CharacteristicForm from "@/components/forms/CharacteristicForm";
import SpecificationForm from "@/components/forms/SpecificationForm";
import PricingForm from "@/components/forms/PricingForm";
import OfferingForm from "@/components/forms/OfferingForm";

type TabType = "characteristic" | "specification" | "pricing" | "offering";

export default function BuilderPage() {
  const [activeTab, setActiveTab] = useState<TabType>("characteristic");

  const tabs = [
    { id: "characteristic", name: "Characteristics", icon: Settings2, component: CharacteristicForm },
    { id: "specification", name: "Specifications", icon: Box, component: SpecificationForm },
    { id: "pricing", name: "Pricing", icon: DollarSign, component: PricingForm },
    { id: "offering", name: "Offerings", icon: ShoppingBag, component: OfferingForm },
  ];

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        {/* Page Header */}
        <div className="flex items-center space-x-4 mb-8 md:mb-12">
          <div className="w-12 h-12 bg-orange-light rounded-2xl flex items-center justify-center border border-orange-brand/10 shadow-inner">
            <LayoutDashboard className="text-orange-brand w-6 h-6" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Builder</h1>
            <p className="text-slate-500 font-medium mt-0.5">Design and publish your product catalog</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex p-1.5 bg-slate-100/80 rounded-2xl mb-10 w-full md:w-fit backdrop-blur-sm border border-slate-200/50">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className="relative flex items-center space-x-2.5 px-5 py-2.5 rounded-xl transition-all outline-none group"
              >
                {isActive && (
                  <motion.div
                    layoutId="active-tab-bg"
                    className="absolute inset-0 bg-white rounded-xl shadow-md border border-slate-200/50"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <span className={`relative z-10 flex items-center space-x-2.5 ${isActive ? "text-orange-brand" : "text-slate-500 group-hover:text-slate-700"}`}>
                  <tab.icon className={`w-4 h-4 transition-transform ${isActive ? "scale-110" : ""}`} />
                  <span className="text-sm font-bold">{tab.name}</span>
                </span>
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10, scale: 0.99 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.99 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="w-full"
          >
            {tabs.map((tab) => (
              activeTab === tab.id && <tab.component key={tab.id} />
            ))}
          </motion.div>
        </AnimatePresence>
      </div>
    </ProtectedRoute>
  );
}
