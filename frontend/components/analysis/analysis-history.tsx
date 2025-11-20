"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { FileText, Clock, CheckCircle, XCircle, ChevronLeft, ChevronRight, Monitor, FileCode } from "lucide-react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";

interface AnalysisSummary {
  total_clauses: number;
  compliant_clauses: number;
  non_compliant_clauses: number;
  compliance_rate: number;
  overall_risk: string;
}

interface AnalysisHistoryItem {
  job_id: string;
  filename: string;
  status: string;
  source: "web_upload" | "word_addin";
  created_at: string;
  updated_at: string;
  summary?: AnalysisSummary;
}

interface AnalysisHistoryResponse {
  success: boolean;
  analyses: AnalysisHistoryItem[];
  pagination: {
    total: number;
    page: number;
    limit: number;
    total_pages: number;
  };
}

export function AnalysisHistory() {
  const router = useRouter();
  const [analyses, setAnalyses] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory();
  }, [page, sourceFilter]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: page.toString(),
        limit: "10",
      });

      if (sourceFilter) {
        params.append("source", sourceFilter);
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/analysis/history?${params}`, {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Failed to fetch analysis history");
      }

      const data: AnalysisHistoryResponse = await response.json();
      setAnalyses(data.analyses);
      setTotalPages(data.pagination.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  const getSourceBadge = (source: "web_upload" | "word_addin") => {
    if (source === "word_addin") {
      return (
        <Badge variant="secondary" className="gap-1">
          <FileCode className="h-3 w-3" />
          Word Add-in
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="gap-1">
        <Monitor className="h-3 w-3" />
        Web Upload
      </Badge>
    );
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <Badge variant="default" className="bg-green-600 gap-1">
            <CheckCircle className="h-3 w-3" />
            Completed
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case "critical":
        return "text-red-600 font-semibold";
      case "high":
        return "text-orange-600 font-semibold";
      case "medium":
        return "text-yellow-600 font-semibold";
      case "low":
        return "text-green-600 font-semibold";
      default:
        return "text-gray-600";
    }
  };

  if (loading && analyses.length === 0) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-20 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            <XCircle className="h-12 w-12 mx-auto mb-2" />
            <p>{error}</p>
            <Button onClick={fetchHistory} className="mt-4">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (analyses.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            <FileText className="h-12 w-12 mx-auto mb-2" />
            <p>No analysis history found</p>
            <p className="text-sm mt-2">Upload a contract to get started</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter Buttons */}
      <div className="flex gap-2">
        <Button
          variant={sourceFilter === null ? "default" : "outline"}
          size="sm"
          onClick={() => setSourceFilter(null)}
        >
          All Sources
        </Button>
        <Button
          variant={sourceFilter === "web_upload" ? "default" : "outline"}
          size="sm"
          onClick={() => setSourceFilter("web_upload")}
        >
          <Monitor className="h-4 w-4 mr-1" />
          Web Upload
        </Button>
        <Button
          variant={sourceFilter === "word_addin" ? "default" : "outline"}
          size="sm"
          onClick={() => setSourceFilter("word_addin")}
        >
          <FileCode className="h-4 w-4 mr-1" />
          Word Add-in
        </Button>
      </div>

      {/* History List */}
      {analyses.map((analysis) => (
        <Card
          key={analysis.job_id}
          className="hover:shadow-lg transition-shadow cursor-pointer"
          onClick={() => router.push(`/results/${analysis.job_id}`)}
        >
          <CardHeader>
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <CardTitle className="text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  {analysis.filename}
                </CardTitle>
                <CardDescription className="flex items-center gap-2 mt-2">
                  <Clock className="h-3 w-3" />
                  {format(new Date(analysis.created_at), "PPpp")}
                </CardDescription>
              </div>
              <div className="flex gap-2">
                {getSourceBadge(analysis.source)}
                {getStatusBadge(analysis.status)}
              </div>
            </div>
          </CardHeader>

          {analysis.summary && (
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Total Clauses</p>
                  <p className="font-semibold text-lg">{analysis.summary.total_clauses || 0}</p>
                </div>
                <div>
                  <p className="text-gray-500">Compliance Rate</p>
                  <p className="font-semibold text-lg">
                    {typeof analysis.summary.compliance_rate === 'number'
                      ? analysis.summary.compliance_rate.toFixed(1)
                      : '0.0'}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Non-Compliant</p>
                  <p className="font-semibold text-lg text-red-600">
                    {analysis.summary.non_compliant_clauses || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          )}
        </Card>
      ))}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center pt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {page + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
}
