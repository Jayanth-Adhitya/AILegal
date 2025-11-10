"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle2, XCircle, RefreshCw, Server } from "lucide-react";
import { Button } from "@/components/ui/button";
import { checkApiHealth } from "@/lib/api";

export default function SettingsPage() {
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");
  const [checking, setChecking] = useState(false);

  const checkStatus = async () => {
    setChecking(true);
    const isHealthy = await checkApiHealth();
    setApiStatus(isHealthy ? "online" : "offline");
    setChecking(false);
  };

  useEffect(() => {
    checkStatus();
  }, []);

  return (
    <div className="h-full p-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="mt-2 text-gray-600">
            Configure your AI Legal Assistant
          </p>
        </div>

        <div className="space-y-6">
          {/* API Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                Backend API Configuration
              </CardTitle>
              <CardDescription>
                Connection settings for the FastAPI backend
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div>
                  <p className="text-sm font-medium text-gray-900">API URL</p>
                  <p className="text-sm text-gray-600">
                    {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                  </p>
                </div>
                <Badge
                  variant={
                    apiStatus === "online"
                      ? "success"
                      : apiStatus === "offline"
                      ? "destructive"
                      : "secondary"
                  }
                >
                  {apiStatus === "online" && (
                    <>
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      Online
                    </>
                  )}
                  {apiStatus === "offline" && (
                    <>
                      <XCircle className="mr-1 h-3 w-3" />
                      Offline
                    </>
                  )}
                  {apiStatus === "checking" && "Checking..."}
                </Badge>
              </div>

              <Button
                variant="outline"
                onClick={checkStatus}
                disabled={checking}
                className="w-full"
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${checking ? "animate-spin" : ""}`} />
                Check Connection
              </Button>

              {apiStatus === "offline" && (
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertDescription>
                    Cannot connect to the backend API. Make sure the FastAPI server is running
                    at {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}.
                  </AlertDescription>
                </Alert>
              )}

              <Alert>
                <AlertDescription className="text-xs">
                  <strong>Configuration:</strong> The API URL is set via the NEXT_PUBLIC_API_URL
                  environment variable. For local development, this defaults to http://localhost:8000.
                  Update the .env.local file to change this setting.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          {/* About */}
          <Card>
            <CardHeader>
              <CardTitle>About</CardTitle>
              <CardDescription>
                Information about the AI Legal Assistant
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium text-gray-900">Version</p>
                <p className="text-sm text-gray-600">1.0.0</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Description</p>
                <p className="text-sm text-gray-600">
                  AI-powered contract review system that analyzes vendor contracts against
                  company policies using advanced language models and vector search.
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Features</p>
                <ul className="mt-2 space-y-1 text-sm text-gray-600">
                  <li>• Automated clause-by-clause analysis</li>
                  <li>• Policy compliance checking</li>
                  <li>• Risk assessment and recommendations</li>
                  <li>• Multiple report formats (Word, HTML)</li>
                  <li>• Real-time progress tracking</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
