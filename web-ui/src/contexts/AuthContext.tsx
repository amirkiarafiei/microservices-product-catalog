"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { apiClient } from "@/lib/api-client";

interface User {
  username: string;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, username: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper to get initial state from localStorage (runs synchronously on first render)
function getInitialToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("token");
  }
  return null;
}

function getInitialUser(): User | null {
  if (typeof window !== "undefined") {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        return JSON.parse(storedUser);
      } catch {
        return null;
      }
    }
  }
  return null;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(getInitialUser);
  const [token, setToken] = useState<string | null>(getInitialToken);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    apiClient.setToken(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("user");
    }
    router.push("/login");
  }, [router]);

  useEffect(() => {
    // Sync apiClient token on mount
    if (token) {
      apiClient.setToken(token);
    }
    
    // Set up unauthorized interceptor
    apiClient.setOnUnauthorized(logout);
  }, [logout, token]);

  const login = (newToken: string, username: string) => {
    const newUser = { username };
    setToken(newToken);
    setUser(newUser);
    apiClient.setToken(newToken);
    localStorage.setItem("user", JSON.stringify(newUser));
    router.push("/builder");
  };

  const contextValue: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
