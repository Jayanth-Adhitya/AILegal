"use client";

import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart3, FileText, ArrowRight } from "lucide-react";

export default function ResultsListPage() {
  return (
    <div className="h-full p-8">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Analysis Results</h1>
          <p className="mt-2 text-gray-600">
            View your contract analysis results and reports
          </p>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-purple-100 p-4">
                <BarChart3 className="h-8 w-8 text-purple-600" />
              </div>
              <div className="flex-1">
                <CardTitle>No Recent Analyses</CardTitle>
                <CardDescription>
                  When you analyze contracts, they will appear here. Results are currently shown
                  only for the most recent analysis.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Button asChild>
                <Link href="/analyze">
                  Analyze Contract
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/">
                  <FileText className="mr-2 h-4 w-4" />
                  Learn More
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="mt-8 rounded-lg border border-blue-200 bg-blue-50 p-6">
          <h3 className="font-semibold text-blue-900">How to Access Results</h3>
          <p className="mt-2 text-sm text-blue-800">
            After analyzing a contract, you&apos;ll be automatically redirected to the results page.
            You can also access your most recent analysis by clicking on the link provided after
            the analysis completes.
          </p>
        </div>
      </div>
    </div>
  );
}
