"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Upload,
  BarChart3,
  Settings,
  Scale,
  LogIn,
  LogOut,
  UserPlus,
  Building2,
  MessageSquare,
  FileEdit,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { LocationIndicator } from "./location-indicator";

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Negotiations",
    href: "/negotiations",
    icon: MessageSquare,
  },
  {
    name: "Documents",
    href: "/documents",
    icon: FileEdit,
  },
  {
    name: "Policies",
    href: "/policies",
    icon: FileText,
  },
  {
    name: "Analyze Contract",
    href: "/analyze",
    icon: Upload,
  },
  {
    name: "Results",
    href: "/results",
    icon: BarChart3,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, loading } = useAuth();

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  return (
    <div className="flex h-full w-64 flex-col bg-card shadow-dual-md">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 px-6">
        <div className="w-14 h-14 relative p-2 rounded-xl shadow-lg backdrop-blur-xl bg-white/30 border border-white/20"
             style={{
               background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(254, 240, 138, 0.2))',
               boxShadow: '0 8px 32px 0 rgba(251, 191, 36, 0.15), inset 0 1px 0 0 rgba(255, 255, 255, 0.5)'
             }}>
          <img
            src="/assets/cirilla-logo.svg"
            alt="Cirilla Logo"
            className="w-full h-full object-contain"
            style={{ filter: 'drop-shadow(0 2px 4px rgba(251, 191, 36, 0.3))' }}
          />
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-900">Cirilla</h1>
          <p className="text-xs text-gray-500">AI Contract Assistant</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-gradient-to-r from-yellow-300 to-yellow-400 text-gray-900 shadow-dual-sm"
                  : "text-gray-700 hover:bg-yellow-100/50 hover:text-gray-900"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 space-y-3">
        {/* User Info or Auth Buttons */}
        {!loading && (
          <>
            {user ? (
              <div className="space-y-3">
                {/* User Info */}
                <div className="rounded-lg bg-yellow-100/50 p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Building2 className="h-4 w-4 text-yellow-700" />
                    <p className="text-sm font-medium text-gray-900">{user.company_name}</p>
                  </div>
                  <p className="text-xs text-gray-600">{user.email}</p>
                  <p className="text-xs text-gray-500 mt-1">ID: {user.company_id}</p>
                </div>

                {/* Logout Button */}
                <Button
                  onClick={handleLogout}
                  variant="outline"
                  className="w-full justify-start"
                  size="sm"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                <Link href="/login" className="block">
                  <Button variant="default" className="w-full justify-start" size="sm">
                    <LogIn className="h-4 w-4 mr-2" />
                    Sign In
                  </Button>
                </Link>
                <Link href="/register" className="block">
                  <Button variant="outline" className="w-full justify-start" size="sm">
                    <UserPlus className="h-4 w-4 mr-2" />
                    Sign Up
                  </Button>
                </Link>
              </div>
            )}
          </>
        )}

        {/* Settings Link */}
        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 transition-all duration-200 hover:bg-yellow-100/50 hover:text-gray-900",
            pathname === "/settings" && "bg-gradient-to-r from-yellow-300 to-yellow-400 text-gray-900 shadow-dual-sm"
          )}
        >
          <Settings className="h-5 w-5" />
          Settings
        </Link>

        {/* Location Indicator */}
        <LocationIndicator />

        {/* API Status */}
        <div className="rounded-lg bg-yellow-200/30 p-3">
          <p className="text-xs font-medium text-yellow-900">API Status</p>
          <p className="mt-1 text-xs text-yellow-700">
            {typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
          </p>
        </div>
      </div>
    </div>
  );
}
