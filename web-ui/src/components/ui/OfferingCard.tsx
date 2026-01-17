"use client";

import React from "react";
import { 
  ArrowRight, 
  Box, 
  DollarSign, 
  Settings2,
  Globe,
  Store,
  Users
} from "lucide-react";
import { motion } from "framer-motion";

interface Characteristic {
  id: string;
  name: string;
  value: string;
  unit_of_measure?: string;
}

interface Specification {
  id: string;
  name: string;
  characteristics?: Characteristic[];
}

interface Price {
  id: string;
  name: string;
  value: number;
  currency: string;
  unit: string;
}

interface Offering {
  id: string;
  name: string;
  description?: string;
  lifecycle_status: string;
  sales_channels?: string[];
  specifications?: Specification[];
  pricing?: Price[];
}

interface OfferingCardProps {
  offering: Offering;
  onClick: () => void;
}

export default function OfferingCard({ offering, onClick }: OfferingCardProps) {
  // Find the lowest price to display
  const lowestPrice = offering.pricing && offering.pricing.length > 0 
    ? offering.pricing.reduce((prev, curr) => prev.value < curr.value ? prev : curr)
    : null;

  // Get top 3 characteristics for display
  const topChars = offering.specifications?.[0]?.characteristics?.slice(0, 3) || [];

  return (
    <motion.div
      whileHover={{ y: -5 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-xl hover:border-orange-brand/20 transition-all group flex flex-col h-full"
    >
      {/* Visual Header */}
      <div className="h-2 bg-orange-brand w-full opacity-0 group-hover:opacity-100 transition-opacity" />
      
      <div className="p-6 md:p-8 flex flex-col flex-grow">
        {/* Status & Channels */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex -space-x-1.5">
            {offering.sales_channels?.map((channel) => (
              <div 
                key={channel} 
                className="w-7 h-7 bg-slate-50 border border-slate-200 rounded-full flex items-center justify-center text-slate-400 group-hover:border-orange-brand/20 group-hover:text-orange-brand transition-colors bg-white shadow-sm"
                title={channel}
              >
                {channel.toLowerCase() === "online" && <Globe className="w-3.5 h-3.5" />}
                {channel.toLowerCase() === "retail" && <Store className="w-3.5 h-3.5" />}
                {channel.toLowerCase() === "partner" && <Users className="w-3.5 h-3.5" />}
              </div>
            ))}
          </div>
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 group-hover:text-orange-brand transition-colors">
            {offering.lifecycle_status}
          </span>
        </div>

        {/* Title & Description */}
        <div className="space-y-2 mb-8">
          <h3 className="text-xl font-extrabold text-slate-900 group-hover:text-orange-brand transition-colors line-clamp-1">
            {offering.name}
          </h3>
          <p className="text-sm text-slate-500 line-clamp-2 leading-relaxed">
            {offering.description || "Premium product offering with exceptional technical specifications and flexible pricing."}
          </p>
        </div>

        {/* Key Attributes */}
        <div className="space-y-3 mb-8 flex-grow">
          {topChars.map((char) => (
            <div key={char.id} className="flex items-center space-x-2 text-xs">
              <div className="w-1 h-1 bg-orange-brand rounded-full" />
              <span className="text-slate-500 font-medium">{char.name}:</span>
              <span className="text-slate-900 font-bold">{char.value} {char.unit_of_measure !== "None" ? char.unit_of_measure : ""}</span>
            </div>
          ))}
          {topChars.length === 0 && (
            <div className="flex items-center space-x-2 text-xs text-slate-400 italic">
              <Settings2 className="w-3 h-3" />
              <span>Technical details included</span>
            </div>
          )}
        </div>

        {/* Price & Action */}
        <div className="pt-6 border-t border-slate-100 flex items-center justify-between mt-auto">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Starting from</p>
            {lowestPrice ? (
              <p className="text-2xl font-black text-slate-900">
                {lowestPrice.value} <span className="text-xs text-orange-brand ml-0.5">{lowestPrice.currency}</span>
              </p>
            ) : (
              <p className="text-sm font-bold text-slate-400">Custom Pricing</p>
            )}
          </div>
          
          <button
            onClick={onClick}
            className="w-12 h-12 bg-slate-900 text-white rounded-2xl flex items-center justify-center hover:bg-orange-brand transition-all shadow-lg shadow-slate-900/10 hover:shadow-orange-brand/30"
          >
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
