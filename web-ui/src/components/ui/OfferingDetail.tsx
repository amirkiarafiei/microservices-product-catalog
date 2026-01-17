"use client";

import React from "react";
import { 
  Box, 
  DollarSign, 
  ShoppingBag, 
  Settings2, 
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  Loader2,
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
  // For cases where they are just IDs
  specification_ids?: string[];
  price_ids?: string[];
}

interface OfferingDetailProps {
  offering: Offering;
  isLoading?: boolean;
}

export default function OfferingDetail({ offering, isLoading }: OfferingDetailProps) {
  const renderStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      DRAFT: "bg-slate-100 text-slate-600 border-slate-200",
      PUBLISHING: "bg-orange-light text-orange-brand border-orange-brand/20 animate-pulse",
      PUBLISHED: "bg-green-50 text-green-700 border-green-200",
      RETIRED: "bg-red-50 text-red-700 border-red-200",
    };
    return (
      <span className={`px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider border rounded-lg ${styles[status] || styles.DRAFT}`}>
        {status}
      </span>
    );
  };

  const getChannelIcon = (channel: string) => {
    switch (channel.toLowerCase()) {
      case "online": return <Globe className="w-4 h-4" />;
      case "retail": return <Store className="w-4 h-4" />;
      case "partner": return <Users className="w-4 h-4" />;
      default: return <ShoppingBag className="w-4 h-4" />;
    }
  };

  if (isLoading && !offering.specifications && !offering.pricing) {
    return (
      <div className="flex flex-col items-center py-20 space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-orange-brand" />
        <p className="text-sm text-slate-400 font-medium tracking-wide">Fetching full details...</p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Header Info */}
      <div className="flex items-start justify-between border-b border-slate-100 pb-8">
        <div className="space-y-2">
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">{offering.name}</h2>
          <p className="text-slate-500 max-w-2xl leading-relaxed">
            {offering.description || "This product offering brings together high-quality specifications and competitive pricing plans to meet your needs."}
          </p>
        </div>
        <div className="flex flex-col items-end space-y-3">
          {renderStatusBadge(offering.lifecycle_status)}
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            ID: {offering.id.slice(0, 8)}
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Specifications Column */}
        <div className="space-y-6">
          <div className="flex items-center space-x-2.5 text-slate-900">
            <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center border border-blue-100">
              <Box className="w-4 h-4 text-blue-600" />
            </div>
            <h3 className="text-lg font-bold">Technical Specifications</h3>
          </div>

          <div className="space-y-4">
            {offering.specifications?.map((spec) => (
              <motion.div 
                key={spec.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
              >
                <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                  <span className="font-bold text-slate-800">{spec.name}</span>
                  <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                </div>
                <div className="p-4 space-y-3">
                  {spec.characteristics?.map((char) => (
                    <div key={char.id} className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-2">
                        <Settings2 className="w-3.5 h-3.5 text-slate-400" />
                        <span className="text-slate-600 font-medium">{char.name}</span>
                      </div>
                      <span className="font-bold text-slate-900">
                        {char.value} {char.unit_of_measure !== "None" ? char.unit_of_measure : ""}
                      </span>
                    </div>
                  ))}
                  {(!spec.characteristics || spec.characteristics.length === 0) && (
                    <p className="text-xs text-slate-400 italic">No characteristics defined.</p>
                  )}
                </div>
              </motion.div>
            ))}
            {(!offering.specifications || offering.specifications.length === 0) && (
              <div className="p-8 bg-slate-50 rounded-2xl border border-dashed border-slate-200 text-center">
                <p className="text-sm text-slate-400 font-medium">No specifications attached.</p>
              </div>
            )}
          </div>
        </div>

        {/* Pricing Column */}
        <div className="space-y-6">
          <div className="flex items-center space-x-2.5 text-slate-900">
            <div className="w-8 h-8 bg-orange-light rounded-lg flex items-center justify-center border border-orange-brand/10">
              <DollarSign className="w-4 h-4 text-orange-brand" />
            </div>
            <h3 className="text-lg font-bold">Pricing Plans</h3>
          </div>

          <div className="space-y-3">
            {offering.pricing?.map((price) => (
              <motion.div 
                key={price.id}
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between hover:border-orange-brand/30 transition-colors group"
              >
                <div className="space-y-1">
                  <p className="font-bold text-slate-800 group-hover:text-orange-brand transition-colors">{price.name}</p>
                  <p className="text-xs text-slate-500 font-medium">{price.unit}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-black text-slate-900">
                    {price.value} <span className="text-sm text-orange-brand ml-0.5">{price.currency}</span>
                  </p>
                </div>
              </motion.div>
            ))}
            {(!offering.pricing || offering.pricing.length === 0) && (
              <div className="p-8 bg-slate-50 rounded-2xl border border-dashed border-slate-200 text-center">
                <p className="text-sm text-slate-400 font-medium">No pricing plans available.</p>
              </div>
            )}
          </div>

          {/* Sales Channels */}
          <div className="pt-8 space-y-4">
            <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Available Via</h4>
            <div className="flex flex-wrap gap-2.5">
              {offering.sales_channels?.map((channel) => (
                <div 
                  key={channel} 
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-bold border border-slate-200 flex items-center space-x-2"
                >
                  {getChannelIcon(channel)}
                  <span>{channel}</span>
                </div>
              ))}
              {(!offering.sales_channels || offering.sales_channels.length === 0) && (
                <p className="text-xs text-slate-400 italic">No sales channels specified.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
