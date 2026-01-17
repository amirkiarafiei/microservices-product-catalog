"use client";

import React, { useState, useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { motion } from "framer-motion";
import { Loader2, Box, Info, RefreshCw, Save, Plus } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";
import MultiSelect from "@/components/ui/MultiSelect";
import { cn } from "@/lib/utils";

const specSchema = z.object({
  name: z.string().min(1, "Name is required"),
  characteristic_ids: z.array(z.string()).min(1, "Select at least one characteristic"),
});

type SpecFormValues = z.infer<typeof specSchema>;

interface Characteristic {
  id: string;
  name: string;
  value: string;
  unit_of_measure: string;
}

interface SpecificationFormProps {
  initialData?: SpecFormValues & { id: string };
  onSuccess?: () => void;
}

export default function SpecificationForm({ initialData, onSuccess }: SpecificationFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [characteristics, setCharacteristics] = useState<Characteristic[]>([]);
  const isEdit = !!initialData;

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SpecFormValues>({
    resolver: zodResolver(specSchema),
    defaultValues: initialData || {
      characteristic_ids: [],
    },
  });

  const fetchCharacteristics = async () => {
    setIsFetching(true);
    try {
      const data = await apiClient.get<Characteristic[]>("/characteristics");
      setCharacteristics(data);
    } catch (error: any) {
      toast.error("Failed to load characteristics");
    } finally {
      setIsFetching(false);
    }
  };

  useEffect(() => {
    fetchCharacteristics();
  }, []);

  const onSubmit = async (data: SpecFormValues) => {
    setIsLoading(true);
    try {
      if (isEdit) {
        await apiClient.put(`/specifications/${initialData.id}`, data);
        toast.success("Specification updated successfully!");
      } else {
        await apiClient.post("/specifications", data);
        toast.success("Specification created successfully!");
        reset();
      }
      if (onSuccess) onSuccess();
    } catch (error: any) {
      toast.error(error.message || `Failed to ${isEdit ? "update" : "create"} specification`);
    } finally {
      setIsLoading(false);
    }
  };

  const charOptions = characteristics.map((c) => ({
    value: c.id,
    label: `${c.name} (${c.value} ${c.unit_of_measure !== "None" ? c.unit_of_measure : ""})`,
  }));

  return (
    <motion.div
      initial={{ opacity: 0, x: isEdit ? 0 : 20 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn("max-w-2xl mx-auto", isEdit && "max-w-full")}
    >
      <div className={cn("bg-white rounded-2xl p-8 border border-slate-100 shadow-sm", isEdit && "p-0 border-0 shadow-none")}>
        {!isEdit && (
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-orange-light rounded-lg flex items-center justify-center">
                <Box className="text-orange-brand w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">New Specification</h2>
                <p className="text-sm text-slate-500">Group characteristics into a technical requirement</p>
              </div>
            </div>
            <button
              onClick={fetchCharacteristics}
              disabled={isFetching}
              type="button"
              className="p-2 text-slate-400 hover:text-orange-brand transition-colors rounded-lg hover:bg-orange-light"
              title="Refresh characteristics"
            >
              <RefreshCw className={cn("w-4 h-4", isFetching && "animate-spin")} />
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="spec-name" className="text-sm font-semibold text-slate-700">Name</label>
            <input
              id="spec-name"
              {...register("name")}
              placeholder="e.g. Fiber High Speed Bundle"
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-4 focus:ring-orange-brand/10 focus:border-orange-brand outline-none transition-all"
            />
            {errors.name && (
              <p className="text-xs text-red-500 font-medium">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="spec-chars" className="text-sm font-semibold text-slate-700">Characteristics</label>
            <Controller
              name="characteristic_ids"
              control={control}
              render={({ field }) => (
                <MultiSelect
                  id="spec-chars"
                  options={charOptions}
                  selected={field.value}
                  onChange={field.onChange}
                  placeholder={isFetching ? "Loading characteristics..." : "Select characteristics..."}
                  disabled={isFetching}
                />
              )}
            />
            {errors.characteristic_ids && (
              <p className="text-xs text-red-500 font-medium">{errors.characteristic_ids.message}</p>
            )}
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-start space-x-3 mt-8">
            <Info className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-500 leading-relaxed">
              Specifications define the technical capabilities of your products. A specification must contain at least one characteristic.
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            disabled={isLoading || isFetching}
            type="submit"
            className="w-full py-3.5 bg-orange-brand hover:bg-orange-hover text-white font-bold rounded-xl shadow-lg shadow-orange-brand/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed mt-4"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                {isEdit ? <Save className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
                <span>{isEdit ? "Update" : "Create"} Specification</span>
              </>
            )}
          </motion.button>
        </form>
      </div>
    </motion.div>
  );
}
