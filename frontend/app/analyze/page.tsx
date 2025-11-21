"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FileCheck, AlertCircle, ArrowRight, Globe, CheckCircle } from "lucide-react";
import { ContractUpload } from "@/components/analysis/contract-upload";
import { AnalysisProgress } from "@/components/analysis/analysis-progress";
import { contractApi, API_BASE_URL } from "@/lib/api";

interface LocationData {
  success: boolean;
  country_code: string | null;
  country_name: string | null;
  region_code: string | null;
  region_name: string | null;
}

export default function AnalyzePage() {
  const [step, setStep] = useState<"upload" | "analyzing">("upload");
  const [contractName, setContractName] = useState("");
  const [jobId, setJobId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [location, setLocation] = useState<LocationData | null>(null);
  const [loadingLocation, setLoadingLocation] = useState(true);

  // Fetch user location on mount
  useEffect(() => {
    fetchLocation();
  }, []);

  const fetchLocation = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/location`, {
        credentials: "include",
      });
      const data: LocationData = await response.json();
      setLocation(data);
    } catch (error) {
      console.error("Failed to fetch location:", error);
    } finally {
      setLoadingLocation(false);
    }
  };

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
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Contract Management</h1>
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

        {/* Regional KB Indicator for Dubai/UAE users */}
        {!loadingLocation && location?.region_code === "dubai_uae" && (
          <Alert className="mb-6 border-blue-200 bg-blue-50">
            <Globe className="h-4 w-4 text-blue-600" />
            <AlertTitle className="text-blue-900">UAE Legal Framework Active</AlertTitle>
            <AlertDescription className="text-blue-800">
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <span>
                    Your analysis will include <strong>UAE Federal Laws and Regulations</strong> from the{" "}
                    <a
                      href="https://www.moet.gov.ae"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-blue-600"
                    >
                      Ministry of Economy
                    </a>
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <span>Regional compliance requirements specific to Dubai and the UAE</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <span>Your company policies and standards</span>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        )}

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
