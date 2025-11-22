"use client";

import { useState, useEffect } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { FileCheck, AlertCircle, ArrowRight, Globe, CheckCircle } from "lucide-react";
import { ContractUpload } from "@/components/analysis/contract-upload";
import { AnalysisProgress } from "@/components/analysis/analysis-progress";
import { ContractChatbot } from "@/components/analysis/contract-chatbot";
import { contractApi, API_BASE_URL } from "@/lib/api";

interface LocationData {
  success: boolean;
  country_code: string | null;
  country_name: string | null;
  region_code: string | null;
  region_name: string | null;
}

export default function AnalyzePage() {
  const [view, setView] = useState<"analyze" | "chat">("analyze");
  const [step, setStep] = useState<"upload" | "analyzing">("upload");
  const [contractName, setContractName] = useState("");
  const [jobId, setJobId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [location, setLocation] = useState<LocationData | null>(null);
  const [loadingLocation, setLoadingLocation] = useState(true);

  // Restore state from sessionStorage on mount
  useEffect(() => {
    const savedState = sessionStorage.getItem("analysisState");
    if (savedState) {
      try {
        const { step: savedStep, contractName: savedName, jobId: savedJobId } = JSON.parse(savedState);
        if (savedJobId) {
          // Check if the job is completed or failed - if so, clear it
          contractApi.getJobStatus(savedJobId).then((jobStatus) => {
            if (jobStatus.status === "completed") {
              // Job is completed, clear the state and don't restore
              sessionStorage.removeItem("analysisState");
            } else if (jobStatus.status === "failed") {
              // Job failed, restore it so user can retry
              setStep(savedStep || "upload");
              setContractName(savedName || "");
              setJobId(savedJobId);
            } else {
              // Job is still processing, restore the state
              setStep(savedStep || "upload");
              setContractName(savedName || "");
              setJobId(savedJobId);
            }
          }).catch((err) => {
            console.error("Failed to check job status:", err);
            // If we can't check status, just clear it to be safe
            sessionStorage.removeItem("analysisState");
          });
        }
      } catch (err) {
        console.error("Failed to restore analysis state:", err);
      }
    }
  }, []);

  // Persist state to sessionStorage whenever it changes
  useEffect(() => {
    if (jobId) {
      sessionStorage.setItem(
        "analysisState",
        JSON.stringify({ step, contractName, jobId })
      );
    }
  }, [step, contractName, jobId]);

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

  const handleUploadSuccess = async (uploadJobId: string, fileName: string) => {
    setJobId(uploadJobId);
    setContractName(fileName);
    setError(null);

    // Automatically start analysis after upload
    await startAnalysis(uploadJobId);
  };

  const startAnalysis = async (analysisJobId: string) => {
    setStarting(true);
    setError(null);

    try {
      await contractApi.analyzeContract(analysisJobId);
      setStep("analyzing");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start analysis");
    } finally {
      setStarting(false);
    }
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

        {/* View Switcher */}
        <div className="mb-6 flex items-center gap-2">
          <button
            onClick={() => setView("analyze")}
            className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
              view === "analyze"
                ? "bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 shadow-dual-sm"
                : "bg-gray-100 text-gray-700 hover:bg-yellow-100/50 hover:text-gray-900"
            }`}
          >
            Analyze Contracts
          </button>
          <button
            onClick={() => setView("chat")}
            className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
              view === "chat"
                ? "bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 shadow-dual-sm"
                : "bg-gray-100 text-gray-700 hover:bg-yellow-100/50 hover:text-gray-900"
            }`}
          >
            Cirilla AI
          </button>
        </div>

        {/* Conditional Rendering based on view */}
        {view === "analyze" ? (
          <>
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
            <span className="text-sm font-medium">Upload & Analyze</span>
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
            <span className="text-sm font-medium">View Results</span>
          </div>
        </div>

        {/* Info Alert */}
        <Alert className="mb-6">
          <FileCheck className="h-4 w-4" />
          <AlertTitle>How Contract Analysis Works</AlertTitle>
          <AlertDescription>
            Upload your contract (DOCX format only) and the analysis will start automatically. Our AI will analyze each clause against your
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
          </div>
        ) : (
          <AnalysisProgress jobId={jobId} contractName={contractName} />
        )}
          </>
        ) : (
          <ContractChatbot />
        )}
      </div>
    </div>
  );
}
