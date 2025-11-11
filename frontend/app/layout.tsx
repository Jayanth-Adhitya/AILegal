'use client'

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { AuthProvider } from "@/contexts/AuthContext";
import { RouteGuard } from "@/components/auth/RouteGuard";
import { usePathname } from "next/navigation";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const isAuthPage = pathname === '/login' || pathname === '/register';

  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <RouteGuard>
            {isAuthPage ? (
              // Auth pages without sidebar
              <main className="h-screen overflow-y-auto bg-gray-50">
                {children}
              </main>
            ) : (
              // App pages with sidebar
              <div className="flex h-screen overflow-hidden">
                <Sidebar />
                <main className="flex-1 overflow-y-auto bg-gray-50">
                  {children}
                </main>
              </div>
            )}
          </RouteGuard>
        </AuthProvider>
      </body>
    </html>
  );
}
