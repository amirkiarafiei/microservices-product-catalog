"use client";

import React, { useState, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { motion } from "framer-motion";
import { 
  Loader2, 
  ShoppingBag, 
  Info, 
  RefreshCw, 
  Save, 
  Send,
  Globe,
  Store,
  Users
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";
import MultiSelect from "@/components/ui/MultiSelect";

const offeringSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  specification_ids: z.array(z.string()),
  price_ids: z.array(z.string()),
  sales_channels: z.array(z.string()),
});

type OfferingFormValues = z.infer<typeof offeringSchema>;

interface Entity {
  id: string;
  name: string;
}

export default function OfferingForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [specs, setSpecs] = useState<Entity[]>([]);
  const [prices, setPrices] = useState<Entity[]>([]);

  const {
    control,
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isValid },
  } = useForm<OfferingFormValues>({
    resolver: zodResolver(offeringSchema),
    mode: "onChange",
    defaultValues: {
      specification_ids: [],
      price_ids: [],
      sales_channels: ["Online"],
    },
  });

  const formData = watch();

  const fetchDependencies = async () => {
    setIsFetching(true);
    try {
      const [specsData, pricesData] = await Promise.all([
        apiClient.get<Entity[]>("/specifications"),
        apiClient.get<Entity[]>("/prices"),
      ]);
      setSpecs(specsData);
      setPrices(pricesData);
    } catch (error: any) {
      toast.error("Failed to load dependencies");
    } finally {
      setIsFetching(false);
    }
  };

  useEffect(() => {
    fetchDependencies();
  }, []);

  const onSaveDraft = async (data: OfferingFormValues) => {
    setIsLoading(true);
    try {
      await apiClient.post("/offerings", data);
      toast.success("Offering draft saved!");
      reset();
    } catch (error: any) {
      toast.error(error.message || "Failed to save draft");
    } finally {
      setIsLoading(false);
    }
  };

  const onPublish = async (data: OfferingFormValues) => {
    // Basic frontend check for publish rules
    if (data.specification_ids.length === 0 || data.price_ids.length === 0 || data.sales_channels.length === 0) {
      toast.error("Cannot publish: Needs at least 1 spec, 1 price, and 1 channel.");
      return;
    }

    setIsLoading(true);
    const loadingToast = toast.loading("Initiating publication saga...");
    try {
      // 1. Create the offering first
      const offering = await apiClient.post<{ id: string }>("/offerings", data);
      
      // 2. Trigger publish saga
      await apiClient.post(`/offerings/${offering.id}/publish`);
      
      toast.success("Publication saga started! Check status in Viewer.", { id: loadingToast });
      reset();
    } catch (error: any) {
      toast.error(error.message || "Failed to initiate publication", { id: loadingToast });
    } finally {
      setIsLoading(false);
    }
  };

  const specOptions = specs.map((s) => ({ value: s.id, label: s.name }));
  const priceOptions = prices.map((p) => ({ value: p.id, label: p.name }));

  const channels = [
    { id: "Online", icon: Globe },
    { id: "Retail", icon: Store },
    { id: "Partner", icon: Users },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="max-w-3xl mx-auto"
    >
      <div className="bg-white rounded-2xl p-8 border border-slate-100 shadow-sm">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-orange-light rounded-lg flex items-center justify-center">
              <ShoppingBag className="text-orange-brand w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">New Product Offering</h2>
              <p className="text-sm text-slate-500">Bundle specs and prices into a marketable product</p>
            </div>
          </div>
          <button
            onClick={fetchDependencies}
            disabled={isFetching}
            className="p-2 text-slate-400 hover:text-orange-brand transition-colors rounded-lg hover:bg-orange-light"
          >
            <RefreshCw className={cn("w-4 h-4", isFetching && "animate-spin")} />
          </button>
        </div>

        <form className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700">Name</label>
            <input
              {...register("name")}
              placeholder="e.g. Fiber Ultra 500"
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all"
            />
            {errors.name && (
              <p className="text-xs text-red-500 font-medium">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700">Description</label>
            <textarea
              {...register("description")}
              rows={3}
              placeholder="Describe the value proposition..."
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Specifications</label>
              <Controller
                name="specification_ids"
                control={control}
                render={({ field }) => (
                  <MultiSelect
                    options={specOptions}
                    selected={field.value}
                    onChange={field.onChange}
                    placeholder={isFetching ? "Loading..." : "Select specs..."}
                    disabled={isFetching}
                  />
                )}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Pricing Plans</label>
              <Controller
                name="price_ids"
                control={control}
                render={({ field }) => (
                  <MultiSelect
                    options={priceOptions}
                    selected={field.value}
                    onChange={field.onChange}
                    placeholder={isFetching ? "Loading..." : "Select prices..."}
                    disabled={isFetching}
                  />
                )}
              />
            </div>
          </div>

          <div className="space-y-3">
            <label className="text-sm font-semibold text-slate-700 block">Sales Channels</label>
            <div className="flex flex-wrap gap-4">
              <Controller
                name="sales_channels"
                control={control}
                render={({ field }) => (
                  <>
                    {channels.map((channel) => (
                      <label
                        key={channel.id}
                        className={cn(
                          "flex items-center space-x-2 px-4 py-2 rounded-xl border cursor-pointer transition-all",
                          field.value.includes(channel.id)
                            ? "bg-orange-light border-orange-brand text-orange-brand"
                            : "bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300"
                        )}
                      >
                        <input
                          type="checkbox"
                          className="hidden"
                          checked={field.value.includes(channel.id)}
                          onChange={() => {
                            const newVals = field.value.includes(channel.id)
                              ? field.value.filter((v) => v !== channel.id)
                              : [...field.value, channel.id];
                            field.onChange(newVals);
                          }}
                        />
                        <channel.icon className="w-4 h-4" />
                        <span className="text-sm font-medium">{channel.id}</span>
                      </label>
                    ))}
                  </>
                )}
              />
            </div>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-start space-x-3 mt-8">
            <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-500 leading-relaxed">
              Publication triggers a distributed saga that validates data across all services. You can save as DRAFT to continue editing later.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-8">
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              disabled={isLoading || isFetching}
              type="button"
              onClick={handleSubmit(onSaveDraft)}
              className="py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition-all flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  <span>Save Draft</span>
                </>
              )}
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              disabled={isLoading || isFetching}
              type="button"
              onClick={handleSubmit(onPublish)}
              className="py-3.5 bg-orange-brand hover:bg-orange-hover text-white font-bold rounded-xl shadow-lg shadow-orange-brand/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  <span>Publish Now</span>
                </>
              )}
            </motion.button>
          </div>
        </form>
      </div>
    </motion.div>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ");
}
