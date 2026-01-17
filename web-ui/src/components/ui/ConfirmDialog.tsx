"use client";

import React from "react";
import Modal from "./Modal";
import { motion } from "framer-motion";
import { AlertTriangle, Loader2 } from "lucide-react";

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isLoading?: boolean;
  variant?: "danger" | "warning" | "primary";
}

export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  isLoading = false,
  variant = "danger",
}: ConfirmDialogProps) {
  const variantStyles = {
    danger: "bg-red-600 hover:bg-red-700 shadow-red-200 text-white",
    warning: "bg-amber-500 hover:bg-amber-600 shadow-amber-200 text-white",
    primary: "bg-orange-brand hover:bg-orange-hover shadow-orange-200 text-white",
  };

  const iconStyles = {
    danger: "text-red-600 bg-red-50",
    warning: "text-amber-500 bg-amber-50",
    primary: "text-orange-brand bg-orange-light",
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="sm">
      <div className="flex flex-col items-center text-center space-y-4">
        <div className={`w-16 h-16 rounded-full flex items-center justify-center ${iconStyles[variant]}`}>
          <AlertTriangle className="w-8 h-8" />
        </div>
        
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-slate-900">{title}</h3>
          <p className="text-slate-500 text-sm leading-relaxed">{message}</p>
        </div>

        <div className="grid grid-cols-2 gap-3 w-full mt-6">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="py-3 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition-all disabled:opacity-50"
          >
            {cancelText}
          </button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onConfirm}
            disabled={isLoading}
            className={`py-3 px-4 font-bold rounded-xl shadow-lg transition-all flex items-center justify-center space-x-2 disabled:opacity-70 ${variantStyles[variant]}`}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <span>{confirmText}</span>
            )}
          </motion.button>
        </div>
      </div>
    </Modal>
  );
}
