"use client";

import { useState, useEffect } from "react";
import { Globe, MapPin } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

interface LocationData {
  success: boolean;
  country_code: string | null;
  country_name: string | null;
  region_code: string | null;
  region_name: string | null;
  ip?: string;
  message?: string;
}

export function LocationIndicator() {
  const [location, setLocation] = useState<LocationData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLocation();
  }, []);

  const fetchLocation = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/location`, {
        credentials: "include",
      });
      const data: LocationData = await response.json();
      setLocation(data);
    } catch (error) {
      console.error("Failed to fetch location:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg bg-blue-100/30 p-3 animate-pulse">
        <div className="h-4 bg-blue-200 rounded w-24 mb-2"></div>
        <div className="h-3 bg-blue-200 rounded w-32"></div>
      </div>
    );
  }

  if (!location?.success || !location.country_code) {
    return (
      <div className="rounded-lg bg-gray-100/50 p-3">
        <div className="flex items-center gap-2 mb-1">
          <Globe className="h-4 w-4 text-gray-500" />
          <p className="text-xs font-medium text-gray-600">Location</p>
        </div>
        <p className="text-xs text-gray-500">Not detected</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-blue-100/30 p-3 border border-blue-200/50">
      <div className="flex items-center gap-2 mb-1">
        <MapPin className="h-4 w-4 text-blue-700" />
        <p className="text-xs font-medium text-blue-900">Your Location</p>
      </div>
      <p className="text-xs font-semibold text-blue-800">
        {location.country_name || location.country_code}
      </p>
      {location.region_name && (
        <p className="text-xs text-blue-600 mt-1">
          📚 {location.region_name} KB Active
        </p>
      )}
    </div>
  );
}
