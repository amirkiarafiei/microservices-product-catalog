"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { motion } from "framer-motion";
import { Loader2, Plus, Info } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";

const charSchema = z.object({
  name: z.string().min(1, "Name is required"),
  value: z.string().min(1, "Value is required"),
  unit_of_measure: z.enum(["Mbps", "GB", "GHz", "Volt", "Watt", "Meter", "None"]),
});

type CharFormValues = z.infer<typeof charSchema>;

export default function CharacteristicForm() {
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CharFormValues>({
    resolver: zodResolver(charSchema),
    defaultValues: {
      unit_of_measure: "None",
    },
  });

  const onSubmit = async (data: CharFormValues) => {
    setIsLoading(true);
    try {
      await apiClient.post("/characteristics", data);
      toast.success("Characteristic created successfully!");
      reset();
    } catch (error: any) {
      toast.error(error.message || "Failed to create characteristic");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="max-w-2xl mx-auto"
    >
      <div className="bg-white rounded-2xl p-8 border border-slate-100 shadow-sm">
        <div className="flex items-center space-x-3 mb-8">
          <div className="w-10 h-10 bg-orange-light rounded-lg flex items-center justify-center">
            <Plus className="text-orange-brand w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">New Characteristic</h2>
            <p className="text-sm text-slate-500">Define an atomic attribute for your products</p>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label htmlFor="char-name" className="text-sm font-semibold text-slate-700">Name</label>
              <input
                {...register("name")}
                id="char-name"
                placeholder="e.g. Download Speed"
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all"
              />
              {errors.name && (
                <p className="text-xs text-red-500 font-medium">{errors.name.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="char-unit" className="text-sm font-semibold text-slate-700">Unit of Measure</label>
              <select
                {...register("unit_of_measure")}
                id="char-unit"
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all appearance-none"
              >
                {["Mbps", "GB", "GHz", "Volt", "Watt", "Meter", "None"].map((unit) => (
                  <option key={unit} value={unit}>
                    {unit}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="char-value" className="text-sm font-semibold text-slate-700">Value</label>
            <input
              {...register("value")}
              id="char-value"
              placeholder="e.g. 100"
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all"
            />
            {errors.value && (
              <p className="text-xs text-red-500 font-medium">{errors.value.message}</p>
            )}
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-start space-x-3 mt-8">
            <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-500 leading-relaxed">
              Characteristics are the building blocks of your catalog. They represent simple, atomic properties that can be grouped into specifications later.
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
                <Plus className="w-5 h-5" />
                <span>Create Characteristic</span>
              </>
            )}
          </motion.button>
        </form>
      </div>
    </motion.div>
  );
}
