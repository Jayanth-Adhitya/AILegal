"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FileCheck, AlertCircle, ArrowRight } from "lucide-react";
import { ContractUpload } from "@/components/analysis/contract-upload";
import { AnalysisProgress } from "@/components/analysis/analysis-progress";
import { contractApi } from "@/lib/api";

export default function AnalyzePage() {
  const [step, setStep] = useState<"upload" | "analyzing">("upload");
  const [contractName, setContractName] = useState("");
  const [jobId, setJobId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const handleUploadSuccess = (uploadJobId: string, fileName: string) => {
    setJobId(uploadJobId);
    setContractName(fileName);
    setError(null);
  };

  const handleStartAnalysis = async () => {
    setStarting(true);
    setError(null);

    try {
      const response = await contractApi.analyzeContract(jobId);
      setStep("analyzing");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis");
    } finally {
      setStarting(false);
    }
  };

  const handleReset = () => {
    setStep("upload");
    setContractName("");
    setJobId("");
    setError(null);
  };

  return (
    <div className="h-full p-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Contract Analysis</h1>
          <p className="mt-2 text-gray-600">
            Upload a contract to analyze it against your company policies
          </p>
        </div>

        {/* Steps Indicator */}
        <div className="mb-8 flex items-center justify-center gap-4">
          <div className="flex items-center gap-2">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full ${
                step === "upload"
                  ? "bg-primary text-white"
                  : "bg-green-600 text-white"
              }`}
            >
              {step === "analyzing" ? "✓" : "1"}
            </div>
            <span className="text-sm font-medium">Upload Contract</span>
          </div>
          <ArrowRight className="h-4 w-4 text-gray-400" />
          <div className="flex items-center gap-2">
            <div
              className={`flex h-8 w-8 items-center justify-center rounded-full ${
                step === "analyzing"
                  ? "bg-primary text-white"
                  : "bg-gray-200 text-gray-600"
              }`}
            >
              2
            </div>
            <span className="text-sm font-medium">Analyze</span>
          </div>
        </div>

        {/* Info Alert */}
        <Alert className="mb-6">
          <FileCheck className="h-4 w-4" />
          <AlertTitle>How Contract Analysis Works</AlertTitle>
          <AlertDescription>
            Upload your contract (DOCX format only). Our AI will analyze each clause against your
            company policies, identify compliance issues, and provide recommendations with tracked
            changes. The analysis typically takes 2-5 minutes depending on contract length.
          </AlertDescription>
        </Alert>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Content */}
        {step === "upload" ? (
          <div className="space-y-6">
            <ContractUpload onUploadSuccess={handleUploadSuccess} />

            {jobId && (
              <Card>
                <CardHeader>
                  <CardTitle>Ready to Analyze</CardTitle>
                  <CardDescription>
                    Contract uploaded successfully. Click below to start the analysis.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4">
                    <Button
                      onClick={handleStartAnalysis}
                      disabled={starting}
                      className="flex-1"
                    >
                      {starting ? "Starting Analysis..." : "Start Analysis"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleReset}
                      disabled={starting}
                    >
                      Upload Different File
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        ) : (
          <AnalysisProgress jobId={jobId} contractName={contractName} />
        )}
      </div>
    </div>
  );
}
