'use client'

import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { AuthProvider } from "@/contexts/AuthContext";
import { RouteGuard } from "@/components/auth/RouteGuard";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { usePathname } from "next/navigation";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  weight: ["400", "500", "600", "700"]
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const isAuthPage = pathname === '/login' || pathname === '/register';
  const isLandingPage = pathname === '/';

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/assets/cirilla-logo.svg" type="image/svg+xml" />
        <title>Cirilla - AI-Powered Contract Assistant</title>
      </head>
      <body className={`${inter.variable} ${spaceGrotesk.variable} font-sans`}>
        <TooltipProvider>
          <AuthProvider>
            <RouteGuard>
              {isLandingPage ? (
                // Landing page - full width, no sidebar, no auth required
                <main className="h-screen overflow-y-auto">
                  {children}
                </main>
              ) : isAuthPage ? (
                // Auth pages without sidebar
                <main className="h-screen overflow-y-auto">
                  {children}
                </main>
              ) : (
                // App pages with sidebar
                <div className="flex h-screen overflow-hidden">
                  <Sidebar />
                  <main className="flex-1 overflow-y-auto bg-background">
                    {children}
                  </main>
                </div>
              )}
            </RouteGuard>
          </AuthProvider>
          <Toaster />
        </TooltipProvider>
      </body>
    </html>
  );
}
