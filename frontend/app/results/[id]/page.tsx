"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Download, FileText, AlertCircle, ArrowLeft } from "lucide-react";
import { StatisticsDashboard } from "@/components/results/statistics-dashboard";
import { ClauseViewer } from "@/components/results/clause-viewer";
import ChatbotFloatingButton from "@/components/chatbot/ChatbotFloatingButton";
import { contractApi } from "@/lib/api";
import { JobStatus } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function ResultsPage() {
  const params = useParams();
  const jobId = params.id as string;
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    const loadResults = async () => {
      setLoading(true);
      setError(null);
      try {
        const jobStatus = await contractApi.getJobStatus(jobId);
        setStatus(jobStatus);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load results");
      } finally {
        setLoading(false);
      }
    };

    loadResults();
  }, [jobId]);

  const handleDownload = async (reportType: "reviewed" | "detailed" | "html") => {
    setDownloading(reportType);
    try {
      const blob = await contractApi.downloadReport(jobId, reportType);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;

      // Set filename based on report type
      const extensions = {
        reviewed: "docx",
        detailed: "docx",
        html: "html",
      };
      link.download = `analysis_report_${jobId}_${reportType}.${extensions[reportType]}`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(null);
    }
  };

  if (loading) {
    return (
      <div className="h-full p-8">
        <div className="mx-auto max-w-7xl space-y-6">
          <Skeleton className="h-12 w-64" />
          <div className="grid gap-4 md:grid-cols-4">
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
          </div>
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (error || !status || !status.result) {
    return (
      <div className="h-full p-8">
        <div className="mx-auto max-w-4xl">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              {error || "Analysis results not found"}
            </AlertDescription>
          </Alert>
          <Button asChild className="mt-4">
            <Link href="/analyze">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Analysis
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const result = status.result;

  return (
    <div className="h-full p-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <div className="mb-2">
              <Button variant="ghost" size="sm" asChild>
                <Link href="/analyze">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Analysis
                </Link>
              </Button>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Analysis Results</h1>
            <p className="mt-2 text-gray-600">
              Contract: {result.contract_name}
            </p>
            <p className="text-sm text-gray-500">
              Analyzed on {result.completed_at ? formatDate(result.completed_at) : formatDate(result.created_at)}
            </p>
          </div>

          {/* Download Reports */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Download Reports</CardTitle>
              <CardDescription className="text-xs">
                Get detailed analysis reports
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownload("reviewed")}
                disabled={!!downloading}
                className="w-full justify-start"
              >
                <FileText className="mr-2 h-4 w-4" />
                {downloading === "reviewed" ? "Downloading..." : "Reviewed Contract"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownload("detailed")}
                disabled={!!downloading}
                className="w-full justify-start"
              >
                <FileText className="mr-2 h-4 w-4" />
                {downloading === "detailed" ? "Downloading..." : "Detailed Report"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownload("html")}
                disabled={!!downloading}
                className="w-full justify-start"
              >
                <Download className="mr-2 h-4 w-4" />
                {downloading === "html" ? "Downloading..." : "HTML Summary"}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Statistics Dashboard */}
        {result.summary && (
          <div className="mb-8">
            <StatisticsDashboard summary={result.summary} />
          </div>
        )}

        {/* Clause-by-Clause Analysis */}
        {result.analysis_results && result.analysis_results.length > 0 && (
          <div>
            <h2 className="mb-4 text-2xl font-bold text-gray-900">
              Clause-by-Clause Analysis
            </h2>
            <ClauseViewer clauses={result.analysis_results} />
          </div>
        )}
      </div>

      {/* Chatbot Floating Button */}
      {status.status === "completed" && <ChatbotFloatingButton jobId={jobId} />}
    </div>
  );
}
