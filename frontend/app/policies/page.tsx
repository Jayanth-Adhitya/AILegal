"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { FileText, RefreshCw, AlertCircle } from "lucide-react";
import { PolicyUpload } from "@/components/policies/policy-upload";
import { PolicyList } from "@/components/policies/policy-list";
import { Policy } from "@/lib/types";
import { policyApi } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reingesting, setReingesting] = useState(false);

  const loadPolicies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await policyApi.getPolicies();
      setPolicies(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load policies");
    } finally {
      setLoading(false);
    }
  };

  const handleReingest = async () => {
    setReingesting(true);
    try {
      await policyApi.reingestPolicies();
      await loadPolicies();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reingest policies");
    } finally {
      setReingesting(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  return (
    <div className="h-full p-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Policy Management</h1>
          <p className="mt-2 text-gray-600">
            Upload and manage your company legal and commercial policies
          </p>
        </div>

        {/* Info Alert */}
        <Alert className="mb-6">
          <FileText className="h-4 w-4" />
          <AlertTitle>How Policy Management Works</AlertTitle>
          <AlertDescription>
            Upload your company policies in TXT, MD, or PDF format. The system will automatically
            extract and index the content for contract analysis. After uploading new policies,
            click &quot;Reingest Policies&quot; to update the vector database.
          </AlertDescription>
        </Alert>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Upload Section */}
        <div className="mb-8">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Upload Policies</h2>
          <PolicyUpload onUploadComplete={loadPolicies} />
        </div>

        {/* Policies List */}
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              Uploaded Policies ({policies.length})
            </h2>
            <Button
              variant="outline"
              onClick={handleReingest}
              disabled={reingesting || policies.length === 0}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${reingesting ? "animate-spin" : ""}`} />
              Reingest Policies
            </Button>
          </div>

          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : (
            <PolicyList policies={policies} onPolicyDeleted={loadPolicies} />
          )}
        </div>
      </div>
    </div>
  );
}
