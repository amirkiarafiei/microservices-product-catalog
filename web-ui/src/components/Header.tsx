"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Menu, 
  X, 
  LayoutDashboard, 
  Layers, 
  ShoppingBag, 
  LogOut, 
  User,
  Package
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

export default function Header() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated && pathname === "/login") return null;

  const navItems = [
    { name: "Builder", href: "/builder", icon: LayoutDashboard },
    { name: "Viewer", href: "/viewer", icon: Layers },
    { name: "Store", href: "/store", icon: ShoppingBag },
  ];

  return (
    <header className="sticky top-0 z-50 w-full bg-white/80 backdrop-blur-md border-b border-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2 group">
            <div className="w-8 h-8 bg-orange-brand rounded-lg flex items-center justify-center transition-transform group-hover:scale-110">
              <Package className="text-white w-5 h-5" />
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600">
              Catalog<span className="text-orange-brand">Hub</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          {isAuthenticated && (
            <nav className="hidden md:flex items-center space-x-1">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "px-4 py-2 rounded-full text-sm font-medium transition-all relative group",
                    pathname.startsWith(item.href)
                      ? "text-orange-brand"
                      : "text-slate-600 hover:text-orange-brand hover:bg-orange-light"
                  )}
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <item.icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </span>
                  {pathname.startsWith(item.href) && (
                    <motion.div
                      layoutId="nav-pill"
                      className="absolute inset-0 bg-orange-light rounded-full z-0"
                      transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                </Link>
              ))}
            </nav>
          )}

          {/* User Section / Auth */}
          <div className="hidden md:flex items-center space-x-4">
            {isAuthenticated ? (
              <div className="flex items-center space-x-4 border-l border-slate-100 pl-4">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center border border-slate-200">
                    <User className="w-4 h-4 text-slate-600" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-semibold text-slate-900 leading-none">
                      {user?.username}
                    </span>
                    <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider mt-0.5">
                      {user?.role || "Administrator"}
                    </span>
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="px-6 py-2 bg-orange-brand text-white text-sm font-semibold rounded-full hover:bg-orange-hover transition-colors shadow-lg shadow-orange-brand/20"
              >
                Sign In
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-white border-t border-slate-100 overflow-hidden"
          >
            <div className="px-4 pt-2 pb-6 space-y-1">
              {isAuthenticated && navItems.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className={cn(
                    "flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-medium transition-colors",
                    pathname.startsWith(item.href)
                      ? "bg-orange-light text-orange-brand"
                      : "text-slate-600 hover:bg-slate-50"
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              ))}
              
              <div className="pt-4 border-t border-slate-100 mt-4">
                {isAuthenticated ? (
                  <div className="flex flex-col space-y-4">
                    <div className="flex items-center space-x-3 px-4">
                      <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center border border-slate-200">
                        <User className="w-5 h-5 text-slate-600" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-base font-semibold text-slate-900">
                          {user?.username}
                        </span>
                        <span className="text-xs text-slate-400">
                          {user?.role || "Administrator"}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setIsOpen(false);
                        logout();
                      }}
                      className="flex items-center space-x-3 w-full px-4 py-3 text-red-600 hover:bg-red-50 rounded-xl transition-colors"
                    >
                      <LogOut className="w-5 h-5" />
                      <span className="font-medium">Logout</span>
                    </button>
                  </div>
                ) : (
                  <Link
                    href="/login"
                    onClick={() => setIsOpen(false)}
                    className="flex items-center justify-center w-full px-4 py-3 bg-orange-brand text-white font-semibold rounded-xl"
                  >
                    Sign In
                  </Link>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
