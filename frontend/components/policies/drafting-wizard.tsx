"use client";

import { DraftPolicyProvider, useDraftPolicy } from "@/contexts/DraftPolicyContext";
import { PolicyTypeSelector } from "./policy-type-selector";
import { Questionnaire } from "./questionnaire";
import { AdditionalNotesStep } from "./additional-notes-step";
import { PolicyPreview } from "./policy-preview";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { CheckCircle2, AlertCircle, Sparkles } from "lucide-react";

function DraftingWizardContent() {
  const { currentStep, error, reset } = useDraftPolicy();

  // Error state
  if (error) {
    return (
      <div className="max-w-3xl mx-auto">
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={reset} variant="outline">
          Start Over
        </Button>
      </div>
    );
  }

  // Success state
  if (currentStep === "saved") {
    return (
      <div className="max-w-2xl mx-auto">
        <Card className="border-2 border-green-200/50 bg-green-50/30">
          <CardContent className="pt-12 pb-12 text-center">
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-gradient-to-r from-green-500 to-green-600 rounded-full">
                <CheckCircle2 className="h-12 w-12 text-white" />
              </div>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Policy Saved Successfully!</h2>
            <p className="text-lg text-gray-600 mb-6">
              Your policy has been saved to your policy library and added to the knowledge base.
            </p>
            <div className="bg-white rounded-lg p-6 border border-green-200">
              <h3 className="font-semibold text-gray-900 mb-2">What's next?</h3>
              <ul className="text-sm text-gray-600 space-y-2 text-left max-w-md mx-auto">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>Your policy is now available in the "Upload Policies" tab</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>It will be used automatically for contract analysis</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>You can chat with Cirilla AI about this policy</span>
                </li>
              </ul>
            </div>
            <div className="mt-8">
              <Button
                onClick={reset}
                className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 hover:from-yellow-500 hover:to-yellow-600 shadow-dual-sm"
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Draft Another Policy
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render appropriate step
  switch (currentStep) {
    case "select-type":
      return <PolicyTypeSelector />;
    case "questions":
      return <Questionnaire />;
    case "notes":
      return <AdditionalNotesStep />;
    case "preview":
      return <PolicyPreview />;
    default:
      return <PolicyTypeSelector />;
  }
}

export function DraftingWizard() {
  return (
    <DraftPolicyProvider>
      <div className="py-6">
        <DraftingWizardContent />
      </div>
    </DraftPolicyProvider>
  );
}
