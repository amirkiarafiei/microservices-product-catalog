"use client";

import React, { useState, useEffect, useCallback } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Layers, 
  Settings2, 
  Box, 
  DollarSign, 
  ShoppingBag,
  Edit2,
  Trash2,
  Eye,
  Lock,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  Loader2,
  Send
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "react-hot-toast";
import DataTable, { Column } from "@/components/ui/DataTable";
import Modal from "@/components/ui/Modal";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import CharacteristicForm from "@/components/forms/CharacteristicForm";
import SpecificationForm from "@/components/forms/SpecificationForm";
import PricingForm from "@/components/forms/PricingForm";
import OfferingForm from "@/components/forms/OfferingForm";
import OfferingDetail from "@/components/ui/OfferingDetail";
import { useSagaPolling } from "@/lib/hooks";

type TabType = "characteristic" | "specification" | "pricing" | "offering";

export default function ViewerPage() {
  const [activeTab, setActiveTab] = useState<TabType>("characteristic");
  const [data, setData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Modal states
  const [editItem, setEditItem] = useState<any>(null);
  const [viewItem, setViewItem] = useState<any>(null);
  const [deleteItem, setDeleteItem] = useState<any>(null);
  const [retireItem, setRetireItem] = useState<any>(null);
  const [publishItem, setPublishItem] = useState<any>(null);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [detailedOffering, setDetailedDetailedOffering] = useState<any>(null);
  const [detailedSpec, setDetailedSpec] = useState<any>(null);
  const { isPolling, pollStatus } = useSagaPolling();

  const tabs = [
    { id: "characteristic", name: "Characteristics", icon: Settings2 },
    { id: "specification", name: "Specifications", icon: Box },
    { id: "pricing", name: "Pricing", icon: DollarSign },
    { id: "offering", name: "Offerings", icon: ShoppingBag },
  ];

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const endpoint = activeTab === "offering" ? "/offerings" : 
                       activeTab === "pricing" ? "/prices" :
                       `/${activeTab}s`;
      const result = await apiClient.get<any[]>(endpoint);
      setData(result);
    } catch (error: any) {
      toast.error(`Failed to fetch ${activeTab}s`);
    } finally {
      setIsLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDelete = async () => {
    if (!deleteItem) return;
    setIsActionLoading(true);
    try {
      const endpoint = activeTab === "offering" ? "/offerings" : 
                       activeTab === "pricing" ? "/prices" :
                       `/${activeTab}s`;
      await apiClient.delete(`${endpoint}/${deleteItem.id}`);
      toast.success(`${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} deleted successfully`);
      fetchData();
      setDeleteItem(null);
    } catch (error: any) {
      toast.error(error.message || "Failed to delete item");
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleRetire = async () => {
    if (!retireItem) return;
    setIsActionLoading(true);
    try {
      await apiClient.post(`/offerings/${retireItem.id}/retire`);
      toast.success("Offering retired successfully");
      fetchData();
      setRetireItem(null);
    } catch (error: any) {
      toast.error(error.message || "Failed to retire offering");
    } finally {
      setIsActionLoading(false);
    }
  };

  const handlePublish = async (item: any) => {
    setIsActionLoading(true);
    const loadingToast = toast.loading(`Initiating publication for "${item.name}"...`);
    try {
      await apiClient.post(`/offerings/${item.id}/publish`);
      pollStatus({
        id: item.id,
        onSuccess: () => fetchData()
      });
      toast.success("Publication saga started!", { id: loadingToast });
      fetchData(); // Update status to PUBLISHING
    } catch (error: any) {
      toast.error(error.message || "Failed to initiate publication", { id: loadingToast });
    } finally {
      setIsActionLoading(false);
    }
  };

  const fetchOfferingDetails = async (offering: any) => {
    setViewItem(offering);
    setIsActionLoading(true);
    try {
      // In a real app, the backend might return the full hierarchy. 
      // Here we might need to fetch specs and prices if they aren't included.
      // For now, we'll assume we fetch the offering by ID which might have more info
      const fullOffering = await apiClient.get<any>(`/offerings/${offering.id}`);
      
      // Also fetch the actual names for specs and prices if the backend only returns IDs
      const [allSpecs, allPrices] = await Promise.all([
        apiClient.get<any[]>("/specifications"),
        apiClient.get<any[]>("/prices"),
      ]);

      const detailed = {
        ...fullOffering,
        specifications: allSpecs.filter(s => fullOffering.specification_ids?.includes(s.id)),
        prices: allPrices.filter(p => fullOffering.price_ids?.includes(p.id)),
      };
      
      setDetailedDetailedOffering(detailed);
    } catch (error: any) {
      toast.error("Failed to load full offering details");
    } finally {
      setIsActionLoading(false);
    }
  };

  const fetchSpecDetails = async (spec: any) => {
    setViewItem(spec);
    setIsActionLoading(true);
    try {
      const fullSpec = await apiClient.get<any>(`/specifications/${spec.id}`);
      const allChars = await apiClient.get<any[]>("/characteristics");
      
      const detailed = {
        ...fullSpec,
        characteristics: allChars.filter(c => fullSpec.characteristic_ids?.includes(c.id)),
      };
      
      setDetailedSpec(detailed);
    } catch (error: any) {
      toast.error("Failed to load specification details");
    } finally {
      setIsActionLoading(false);
    }
  };

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

  // Column Definitions
  const columns: Record<TabType, Column<any>[]> = {
    characteristic: [
      { header: "Name", accessor: "name", sortable: true, className: "font-bold text-slate-900" },
      { header: "Value", accessor: "value", sortable: true },
      { header: "Unit", accessor: "unit_of_measure", sortable: true },
      { header: "Created", accessor: (item) => new Date(item.created_at).toLocaleDateString() },
      {
        header: "Actions",
        accessor: (item) => (
          <div className="flex items-center space-x-2">
            <button onClick={() => setEditItem(item)} className="p-2 text-slate-400 hover:text-orange-brand hover:bg-orange-light rounded-lg transition-all">
              <Edit2 className="w-4 h-4" />
            </button>
            <button onClick={() => setDeleteItem(item)} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ),
      },
    ],
    specification: [
      { header: "Name", accessor: "name", sortable: true, className: "font-bold text-slate-900" },
      { 
        header: "Characteristics", 
        accessor: (item) => (
          <div className="flex flex-wrap gap-1 max-w-xs">
            {item.characteristic_ids?.length || 0} items
          </div>
        ) 
      },
      { header: "Created", accessor: (item) => new Date(item.created_at).toLocaleDateString() },
      {
        header: "Actions",
        accessor: (item) => (
          <div className="flex items-center space-x-2">
            <button onClick={() => fetchSpecDetails(item)} className="p-2 text-slate-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-all">
              <Eye className="w-4 h-4" />
            </button>
            <button onClick={() => setEditItem(item)} className="p-2 text-slate-400 hover:text-orange-brand hover:bg-orange-light rounded-lg transition-all">
              <Edit2 className="w-4 h-4" />
            </button>
            <button onClick={() => setDeleteItem(item)} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ),
      },
    ],
    pricing: [
      { header: "Name", accessor: "name", sortable: true, className: "font-bold text-slate-900" },
      { header: "Price", accessor: (item) => `${item.value} ${item.currency}`, sortable: true },
      { header: "Unit", accessor: "unit", sortable: true },
      { 
        header: "Status", 
        accessor: (item) => (
          <div className="flex items-center space-x-1.5">
            {item.locked ? (
              <div className="flex items-center space-x-1.5 text-amber-600 bg-amber-50 px-2 py-1 rounded-lg border border-amber-100">
                <Lock className="w-3 h-3" />
                <span className="text-[10px] font-bold uppercase tracking-wider">Locked</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1.5 text-green-600 bg-green-50 px-2 py-1 rounded-lg border border-green-100">
                <ShieldCheck className="w-3 h-3" />
                <span className="text-[10px] font-bold uppercase tracking-wider">Available</span>
              </div>
            )}
          </div>
        ) 
      },
      {
        header: "Actions",
        accessor: (item) => (
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => !item.locked && setEditItem(item)} 
              disabled={item.locked}
              className={`p-2 rounded-lg transition-all ${item.locked ? "text-slate-200 cursor-not-allowed" : "text-slate-400 hover:text-orange-brand hover:bg-orange-light"}`}
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button 
              onClick={() => !item.locked && setDeleteItem(item)} 
              disabled={item.locked}
              className={`p-2 rounded-lg transition-all ${item.locked ? "text-slate-200 cursor-not-allowed" : "text-slate-400 hover:text-red-500 hover:bg-red-50"}`}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ),
      },
    ],
    offering: [
      { header: "Name", accessor: "name", sortable: true, className: "font-bold text-slate-900" },
      { header: "Status", accessor: (item) => renderStatusBadge(item.lifecycle_status), sortable: true },
      { header: "Created", accessor: (item) => new Date(item.created_at).toLocaleDateString() },
      {
        header: "Actions",
        accessor: (item) => (
          <div className="flex items-center space-x-2">
            <button onClick={() => fetchOfferingDetails(item)} className="p-2 text-slate-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-all">
              <Eye className="w-4 h-4" />
            </button>
            {item.lifecycle_status === "DRAFT" && (
              <>
                <button 
                  onClick={() => handlePublish(item)} 
                  disabled={isActionLoading}
                  className="p-2 text-slate-400 hover:text-green-500 hover:bg-green-50 rounded-lg transition-all"
                  title="Publish Now"
                >
                  <Send className="w-4 h-4" />
                </button>
                <button onClick={() => setEditItem(item)} className="p-2 text-slate-400 hover:text-orange-brand hover:bg-orange-light rounded-lg transition-all">
                  <Edit2 className="w-4 h-4" />
                </button>
                <button onClick={() => setDeleteItem(item)} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all">
                  <Trash2 className="w-4 h-4" />
                </button>
              </>
            )}
            {item.lifecycle_status === "PUBLISHED" && (
              <button 
                onClick={() => setRetireItem(item)} 
                className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                title="Retire Offering"
              >
                <ShieldAlert className="w-4 h-4" />
              </button>
            )}
          </div>
        ),
      },
    ],
  };

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        {/* Page Header */}
        <div className="flex items-center space-x-4 mb-8 md:mb-12">
          <div className="w-12 h-12 bg-orange-light rounded-2xl flex items-center justify-center border border-orange-brand/10 shadow-inner">
            <Layers className="text-orange-brand w-6 h-6" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Viewer</h1>
            <p className="text-slate-500 font-medium mt-0.5">Manage your existing product catalog entities</p>
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
                    layoutId="active-tab-bg-viewer"
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

        {/* Content Table */}
        <DataTable
          data={data}
          columns={columns[activeTab]}
          isLoading={isLoading}
          pageSize={20}
          searchPlaceholder={`Search ${activeTab}s...`}
          emptyMessage={`No ${activeTab}s found. Start by creating one in the Builder.`}
        />

        {/* Edit Modals */}
        <Modal
          isOpen={!!editItem}
          onClose={() => setEditItem(null)}
          title={`Edit ${activeTab}`}
          size={activeTab === "offering" ? "lg" : "md"}
        >
          {activeTab === "characteristic" && (
            <CharacteristicForm 
              initialData={editItem} 
              onSuccess={() => { setEditItem(null); fetchData(); }} 
            />
          )}
          {activeTab === "specification" && (
            <SpecificationForm 
              initialData={editItem} 
              onSuccess={() => { setEditItem(null); fetchData(); }} 
            />
          )}
          {activeTab === "pricing" && (
            <PricingForm 
              initialData={editItem} 
              onSuccess={() => { setEditItem(null); fetchData(); }} 
            />
          )}
          {activeTab === "offering" && (
            <OfferingForm 
              initialData={editItem} 
              onSuccess={() => { setEditItem(null); fetchData(); }} 
            />
          )}
        </Modal>

        {/* Delete Confirmation */}
        <ConfirmDialog
          isOpen={!!deleteItem}
          onClose={() => setDeleteItem(null)}
          onConfirm={handleDelete}
          title={`Delete ${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}?`}
          message={`Are you sure you want to delete "${deleteItem?.name}"? This action cannot be undone.`}
          isLoading={isActionLoading}
        />

        {/* Retire Confirmation */}
        <ConfirmDialog
          isOpen={!!retireItem}
          onClose={() => setRetireItem(null)}
          onConfirm={handleRetire}
          title="Retire Offering?"
          message={`Are you sure you want to retire "${retireItem?.name}"? It will no longer be visible in the marketplace.`}
          variant="warning"
          confirmText="Retire"
          isLoading={isActionLoading}
        />

        {/* Detail Modal (Offering or Spec) */}
        <Modal
          isOpen={!!viewItem}
          onClose={() => { setViewItem(null); setDetailedDetailedOffering(null); setDetailedSpec(null); }}
          title={`${activeTab === "offering" ? "Product Offering" : "Specification"} Details`}
          size="lg"
        >
          {viewItem && activeTab === "specification" && (
            <div className="space-y-8">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <h2 className="text-2xl font-bold text-slate-900">{viewItem.name}</h2>
                  <p className="text-slate-500">Technical Specification details.</p>
                </div>
              </div>

              {isActionLoading && !detailedSpec ? (
                <div className="flex flex-col items-center py-12 space-y-4">
                  <Loader2 className="w-8 h-8 animate-spin text-orange-brand" />
                  <p className="text-sm text-slate-400 font-medium">Loading details...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 text-slate-900 font-bold border-b border-slate-100 pb-2">
                    <Settings2 className="w-4 h-4" />
                    <span>Included Characteristics</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {detailedSpec?.characteristics?.map((char: any) => (
                      <div key={char.id} className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-center justify-between">
                        <div className="space-y-0.5">
                          <p className="font-bold text-slate-800 text-sm">{char.name}</p>
                          <p className="text-xs text-slate-500">Value: {char.value} {char.unit_of_measure !== "None" ? char.unit_of_measure : ""}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {viewItem && activeTab === "offering" && (
            <OfferingDetail offering={detailedOffering || viewItem} isLoading={isActionLoading} />
          )}
        </Modal>
      </div>
    </ProtectedRoute>
  );
}
