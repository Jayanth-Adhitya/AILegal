"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Sparkles, Loader2 } from "lucide-react";
import { useDraftPolicy } from "@/contexts/DraftPolicyContext";
import { policyApi } from "@/lib/api";

export function AdditionalNotesStep() {
  const {
    additionalNotes,
    setAdditionalNotes,
    answers,
    selectedPolicyType,
    setGeneratedPolicy,
    setCurrentStep,
    loading,
    setLoading,
    setError,
  } = useDraftPolicy();

  const handleGenerate = async () => {
    if (!selectedPolicyType) return;

    setLoading(true);
    setError(null);

    try {
      const response = await policyApi.generatePolicy(selectedPolicyType, answers, additionalNotes || undefined);

      setGeneratedPolicy({
        title: response.title,
        content: response.content,
        sections: response.sections,
        metadata: response.metadata,
        version: response.version,
      });

      setCurrentStep("preview");
    } catch (err) {
      console.error("Failed to generate policy:", err);
      setError(err instanceof Error ? err.message : "Failed to generate policy");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setCurrentStep("questions");
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Card className="border-2 border-yellow-200/50 shadow-dual-sm">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-yellow-400 to-yellow-500 rounded-lg">
              <Sparkles className="h-6 w-6 text-gray-900" />
            </div>
            <div>
              <CardTitle className="text-2xl">Additional Notes (Optional)</CardTitle>
              <CardDescription className="text-base mt-1">
                Add any extra context, special requirements, or details you'd like to include
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Your Notes</label>
            <Textarea
              value={additionalNotes}
              onChange={(e) => setAdditionalNotes(e.target.value)}
              placeholder="Example: This policy should emphasize remote work flexibility while maintaining data security. Include specific provisions for international contractors..."
              className="min-h-[200px] border-gray-300 focus:border-yellow-400 focus:ring-yellow-400"
            />
            <p className="text-xs text-gray-500">
              These notes will help Cirilla AI tailor the policy to your specific needs
            </p>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">What happens next?</h4>
            <p className="text-sm text-gray-700">
              Based on your answers{additionalNotes && " and notes"}, Cirilla AI will generate a comprehensive,
              professional policy document. This typically takes 10-20 seconds.
            </p>
          </div>

          <div className="flex justify-between gap-3 pt-4">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={loading}
              className="border-gray-300"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Questions
            </Button>
            <Button
              onClick={handleGenerate}
              disabled={loading}
              className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 hover:from-yellow-500 hover:to-yellow-600 shadow-dual-sm"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating Policy...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Policy
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary card */}
      <Card className="border-gray-200">
        <CardHeader>
          <CardTitle className="text-lg">Your Answers Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="text-sm text-gray-600">
              <span className="font-medium text-gray-900">Questions answered:</span> {answers.length}
            </div>
            <div className="max-h-[300px] overflow-y-auto space-y-2">
              {answers.map((answer, index) => (
                <div key={answer.question_id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="text-xs font-medium text-gray-500 mb-1">Question {index + 1}</div>
                  <div className="text-sm font-medium text-gray-900 mb-1">{answer.question_text}</div>
                  <div className="text-sm text-gray-700">
                    {Array.isArray(answer.value) ? answer.value.join(", ") : answer.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
