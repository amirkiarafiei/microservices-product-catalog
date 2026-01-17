"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { motion } from "framer-motion";
import { Loader2, DollarSign, Info, Save, Plus } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";
import { cn } from "@/lib/utils";

const pricingSchema = z.object({
  name: z.string().min(1, "Name is required"),
  value: z.number().positive("Price must be positive"),
  unit: z.string().min(1, "Unit is required"),
  currency: z.enum(["USD", "EUR", "TRY"]),
});

type PricingFormValues = z.infer<typeof pricingSchema>;

interface PricingFormProps {
  initialData?: PricingFormValues & { id: string };
  onSuccess?: () => void;
}

export default function PricingForm({ initialData, onSuccess }: PricingFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const isEdit = !!initialData;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PricingFormValues>({
    resolver: zodResolver(pricingSchema),
    defaultValues: initialData || {
      currency: "USD",
      unit: "per month",
      value: 0,
    },
  });

  const onSubmit = async (data: PricingFormValues) => {
    setIsLoading(true);
    try {
      if (isEdit) {
        await apiClient.put(`/prices/${initialData.id}`, data);
        toast.success("Pricing plan updated successfully!");
      } else {
        await apiClient.post("/prices", data);
        toast.success("Pricing plan created successfully!");
        reset();
      }
      if (onSuccess) onSuccess();
    } catch (error: any) {
      toast.error(error.message || `Failed to ${isEdit ? "update" : "create"} pricing`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: isEdit ? 0 : 20 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn("max-w-2xl mx-auto", isEdit && "max-w-full")}
    >
      <div className={cn("bg-white rounded-2xl p-8 border border-slate-100 shadow-sm", isEdit && "p-0 border-0 shadow-none")}>
        {!isEdit && (
          <div className="flex items-center space-x-3 mb-8">
            <div className="w-10 h-10 bg-orange-light rounded-lg flex items-center justify-center">
              <DollarSign className="text-orange-brand w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">New Pricing Plan</h2>
              <p className="text-sm text-slate-500">Define monetary costs for your offerings</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="price-name" className="text-sm font-semibold text-slate-700">Name</label>
            <input
              id="price-name"
              {...register("name")}
              placeholder="e.g. Monthly Fiber Basic"
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all"
            />
            {errors.name && (
              <p className="text-xs text-red-500 font-medium">{errors.name.message}</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label htmlFor="price-value" className="text-sm font-semibold text-slate-700">Price Value</label>
              <div className="relative">
                <input
                  id="price-value"
                  {...register("value", { valueAsNumber: true })}
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  className="w-full pl-8 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all"
                />
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-medium">$</span>
              </div>
              {errors.value && (
                <p className="text-xs text-red-500 font-medium">{errors.value.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="price-currency" className="text-sm font-semibold text-slate-700">Currency</label>
              <select
                id="price-currency"
                {...register("currency")}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all appearance-none"
              >
                {["USD", "EUR", "TRY"].map((curr) => (
                  <option key={curr} value={curr}>
                    {curr}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="price-unit" className="text-sm font-semibold text-slate-700">Unit</label>
            <input
              id="price-unit"
              {...register("unit")}
              placeholder="e.g. per month"
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all"
            />
            {errors.unit && (
              <p className="text-xs text-red-500 font-medium">{errors.unit.message}</p>
            )}
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-start space-x-3 mt-8">
            <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-500 leading-relaxed">
              Pricing plans can be reused across different product offerings. When an offering is published, its associated prices are locked.
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            disabled={isLoading}
            type="submit"
            className="w-full py-3.5 bg-orange-brand hover:bg-orange-hover text-white font-bold rounded-xl shadow-lg shadow-orange-brand/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed mt-4"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                {isEdit ? <Save className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
                <span>{isEdit ? "Update" : "Create"} Pricing Plan</span>
              </>
            )}
          </motion.button>
        </form>
      </div>
    </motion.div>
  );
}
