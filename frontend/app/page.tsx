"use client";

import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Upload, BarChart3, Shield, CheckCircle2, AlertCircle } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="h-full p-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Welcome to AI Legal Assistant</h1>
          <p className="mt-2 text-gray-600">
            Automate contract review with AI-powered analysis against your company policies
          </p>
        </div>

        {/* Quick Actions */}
        <div className="mb-8 grid gap-6 md:grid-cols-3">
          <Link href="/policies">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center gap-4">
                  <div className="rounded-lg bg-blue-100 p-3">
                    <FileText className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <CardTitle>Manage Policies</CardTitle>
                    <CardDescription>Upload and organize company policies</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>
          </Link>

          <Link href="/analyze">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center gap-4">
                  <div className="rounded-lg bg-green-100 p-3">
                    <Upload className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <CardTitle>Analyze Contract</CardTitle>
                    <CardDescription>Review contracts against policies</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>
          </Link>

          <Link href="/results">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center gap-4">
                  <div className="rounded-lg bg-purple-100 p-3">
                    <BarChart3 className="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <CardTitle>View Results</CardTitle>
                    <CardDescription>See analysis results and reports</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>
          </Link>
        </div>

        {/* Features Section */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" />
                How It Works
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="space-y-3 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    1
                  </span>
                  <span>
                    <strong>Upload Policies:</strong> Add your company legal and commercial policies
                    in PDF, TXT, or MD format
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    2
                  </span>
                  <span>
                    <strong>Submit Contract:</strong> Upload vendor/company contracts for analysis
                    (DOCX format)
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    3
                  </span>
                  <span>
                    <strong>AI Analysis:</strong> Our system reviews each clause against your
                    policies using advanced AI
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    4
                  </span>
                  <span>
                    <strong>Review Results:</strong> Get detailed reports with redlines, comments,
                    and recommendations
                  </span>
                </li>
              </ol>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                Key Features
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
                  <span>Automated clause-by-clause contract analysis</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
                  <span>Policy compliance checking with risk assessment</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
                  <span>Track changes and redline suggestions</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
                  <span>Detailed reports with policy references</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
                  <span>Real-time progress tracking during analysis</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
                  <span>Multiple export formats (Word, HTML)</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Get Started CTA */}
        <Card className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-center">Ready to Get Started?</CardTitle>
            <CardDescription className="text-center">
              Begin by uploading your company policies or jump straight to analyzing a contract
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center gap-4">
            <Button asChild>
              <Link href="/policies">Upload Policies</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/analyze">Analyze Contract</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
