"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowRight, History } from "lucide-react";
import { AnalysisHistory } from "@/components/analysis/analysis-history";

export default function ResultsListPage() {
  return (
    <div className="h-full p-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <History className="h-8 w-8" />
            Analysis History
          </h1>
          <p className="mt-2 text-gray-600">
            View all your contract analysis results from web uploads and Word add-in
          </p>
        </div>

        <div className="mb-6">
          <Button asChild>
            <Link href="/analyze">
              Analyze New Contract
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>

        <AnalysisHistory />

        <div className="mt-8 rounded-lg border border-blue-200 bg-blue-50 p-6">
          <h3 className="font-semibold text-blue-900">About Analysis History</h3>
          <ul className="mt-2 space-y-1 text-sm text-blue-800">
            <li>• All your analysis results are automatically saved</li>
            <li>• Analyses from the Word add-in are marked with a special badge</li>
            <li>• Click on any analysis to view full details</li>
            <li>• Use the filter buttons to view only web uploads or Word add-in analyses</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
