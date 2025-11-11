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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

const navigation = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Negotiations",
    href: "/negotiations",
    icon: MessageSquare,
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
    <div className="flex h-full w-64 flex-col border-r bg-white">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <Scale className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-lg font-bold text-gray-900">Legal Assistant</h1>
          <p className="text-xs text-gray-500">AI-Powered</p>
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
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t p-4 space-y-3">
        {/* User Info or Auth Buttons */}
        {!loading && (
          <>
            {user ? (
              <div className="space-y-3">
                {/* User Info */}
                <div className="rounded-lg bg-gray-50 p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Building2 className="h-4 w-4 text-gray-600" />
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
            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 hover:text-gray-900",
            pathname === "/settings" && "bg-primary text-primary-foreground"
          )}
        >
          <Settings className="h-5 w-5" />
          Settings
        </Link>

        {/* API Status */}
        <div className="rounded-lg bg-blue-50 p-3">
          <p className="text-xs font-medium text-blue-900">API Status</p>
          <p className="mt-1 text-xs text-blue-700">
            {typeof window !== "undefined" && process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
          </p>
        </div>
      </div>
    </div>
  );
}
