"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle2, AlertCircle, Loader2, FileCheck } from "lucide-react";
import { contractApi } from "@/lib/api";
import { JobStatus } from "@/lib/types";

interface AnalysisProgressProps {
  jobId: string;
  contractName: string;
}

export function AnalysisProgress({ jobId, contractName }: AnalysisProgressProps) {
  const router = useRouter();
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const jobStatus = await contractApi.getJobStatus(jobId);
        setStatus(jobStatus);

        if (jobStatus.status === "completed") {
          clearInterval(pollInterval);
          // Wait a moment then redirect to results
          setTimeout(() => {
            router.push(`/results/${jobId}`);
          }, 2000);
        } else if (jobStatus.status === "failed") {
          clearInterval(pollInterval);
          setError(jobStatus.message || "Analysis failed");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to check status");
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [jobId, router]);

  const getStatusIcon = () => {
    switch (status?.status) {
      case "completed":
        return <CheckCircle2 className="h-12 w-12 text-green-600" />;
      case "failed":
        return <AlertCircle className="h-12 w-12 text-red-600" />;
      case "processing":
        return <Loader2 className="h-12 w-12 animate-spin text-primary" />;
      default:
        return <FileCheck className="h-12 w-12 text-gray-400" />;
    }
  };

  const getStatusMessage = () => {
    switch (status?.status) {
      case "completed":
        return "Analysis completed successfully!";
      case "failed":
        return "Analysis failed";
      case "processing":
        return "Analyzing contract...";
      default:
        return "Preparing analysis...";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Contract Analysis in Progress</CardTitle>
        <CardDescription>Analyzing: {contractName}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex flex-col items-center justify-center py-8">
          {getStatusIcon()}
          <p className="mt-4 text-lg font-medium text-gray-900">
            {getStatusMessage()}
          </p>
          {status?.message && (
            <p className="mt-2 text-sm text-gray-600">{status.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Progress</span>
            <span className="font-medium text-gray-900">
              {status?.progress || 0}%
            </span>
          </div>
          <Progress value={status?.progress || 0} className="h-2" />
        </div>

        {status?.status === "completed" && (
          <Alert className="bg-green-50 border-green-200">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Analysis complete! Redirecting to results...
            </AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {status?.status === "completed" && (
          <Button onClick={() => router.push(`/results/${jobId}`)} className="w-full">
            View Results
          </Button>
        )}

        {status?.status === "failed" && (
          <Button variant="outline" onClick={() => router.push("/analyze")} className="w-full">
            Try Again
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
