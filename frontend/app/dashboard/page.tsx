"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Upload,
  BarChart3,
  Shield,
  CheckCircle2,
  MessageSquare,
  Users,
  FolderOpen,
} from "lucide-react";
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
} from "@/lib/animations";

export default function Dashboard() {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="h-full p-8"
    >
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <motion.div variants={fadeInUp} className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome to Cirilla
          </h1>
          <p className="mt-2 text-gray-600">
            Automate contract review with AI-powered analysis against your
            company policies
          </p>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          variants={staggerContainer}
          className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4"
        >
          <motion.div variants={staggerItem}>
            <Link href="/policies">
              <Card className="h-full cursor-pointer transition-transform hover:scale-[1.02]">
                <CardHeader>
                  <div className="flex items-center gap-4">
                    <div className="rounded-lg bg-yellow-200/50 p-3">
                      <FileText className="h-6 w-6 text-yellow-700" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">Manage Policies</CardTitle>
                      <CardDescription>
                        Upload and organize policies
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          </motion.div>

          <motion.div variants={staggerItem}>
            <Link href="/analyze">
              <Card className="h-full cursor-pointer transition-transform hover:scale-[1.02]">
                <CardHeader>
                  <div className="flex items-center gap-4">
                    <div className="rounded-lg bg-green-200/50 p-3">
                      <Upload className="h-6 w-6 text-green-700" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">Analyze Contract</CardTitle>
                      <CardDescription>
                        Review against policies
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          </motion.div>

          <motion.div variants={staggerItem}>
            <Link href="/results">
              <Card className="h-full cursor-pointer transition-transform hover:scale-[1.02]">
                <CardHeader>
                  <div className="flex items-center gap-4">
                    <div className="rounded-lg bg-purple-200/50 p-3">
                      <BarChart3 className="h-6 w-6 text-purple-700" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">View Results</CardTitle>
                      <CardDescription>
                        Analysis reports
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          </motion.div>

          <motion.div variants={staggerItem}>
            <Link href="/negotiations">
              <Card className="h-full cursor-pointer transition-transform hover:scale-[1.02]">
                <CardHeader>
                  <div className="flex items-center gap-4">
                    <div className="rounded-lg bg-blue-200/50 p-3">
                      <Users className="h-6 w-6 text-blue-700" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">Negotiations</CardTitle>
                      <CardDescription>
                        AI-powered discussions
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            </Link>
          </motion.div>
        </motion.div>

        {/* Features Section */}
        <motion.div
          variants={staggerContainer}
          className="grid gap-6 md:grid-cols-2"
        >
          <motion.div variants={staggerItem}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-yellow-600" />
                  How It Works
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-3 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-yellow-200/50 text-xs font-semibold text-yellow-700">
                      1
                    </span>
                    <span>
                      <strong>Upload Policies:</strong> Add your company legal
                      and commercial policies in PDF, TXT, or MD format
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-yellow-200/50 text-xs font-semibold text-yellow-700">
                      2
                    </span>
                    <span>
                      <strong>Submit Contract:</strong> Upload vendor/company
                      contracts for analysis (DOCX format)
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-yellow-200/50 text-xs font-semibold text-yellow-700">
                      3
                    </span>
                    <span>
                      <strong>AI Analysis:</strong> Our system reviews each
                      clause against your policies using advanced AI
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-yellow-200/50 text-xs font-semibold text-yellow-700">
                      4
                    </span>
                    <span>
                      <strong>Review Results:</strong> Get detailed reports with
                      redlines, comments, and recommendations
                    </span>
                  </li>
                </ol>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={staggerItem}>
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
          </motion.div>
        </motion.div>

        {/* Get Started CTA */}
        <motion.div variants={fadeInUp}>
          <Card className="mt-8 bg-gradient-to-r from-yellow-100 to-yellow-200/50">
            <CardHeader>
              <CardTitle className="text-center">Ready to Get Started?</CardTitle>
              <CardDescription className="text-center">
                Begin by uploading your company policies or jump straight to
                analyzing a contract
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
        </motion.div>
      </div>
    </motion.div>
  );
}
