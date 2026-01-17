"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    // Redirect based on authentication status
    if (isAuthenticated) {
      router.replace("/builder");
    } else {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold text-orange-brand">TMF Product Catalog</h1>
      <div className="mt-4 flex items-center space-x-2">
        <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        <p className="text-xl text-slate-500">Redirecting...</p>
      </div>
    </main>
  );
}
