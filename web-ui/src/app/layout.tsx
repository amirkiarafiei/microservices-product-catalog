import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TMF Product Catalog",
  description: "Enterprise Product Catalog Management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: "#fff",
                color: "#1e293b",
                borderRadius: "12px",
                border: "1px solid #f1f5f9",
                boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                fontSize: "14px",
                padding: "12px 16px",
              },
              success: {
                iconTheme: {
                  primary: "#FF7900",
                  secondary: "#fff",
                },
              },
            }}
          />
          <div className="min-h-screen flex flex-col bg-slate-50/50">
            <Header />
            <main className="flex-grow">
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
