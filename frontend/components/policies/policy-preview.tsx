"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Download, Save, RefreshCw, Edit2, FileText, CheckCircle2, Loader2 } from "lucide-react";
import { useDraftPolicy } from "@/contexts/DraftPolicyContext";
import { policyApi } from "@/lib/api";
import ReactMarkdown from "react-markdown";

export function PolicyPreview() {
  const {
    generatedPolicy,
    selectedPolicyType,
    selectedPolicyTypeName,
    setCurrentStep,
    setLoading,
    loading,
    setError,
    reset,
  } = useDraftPolicy();

  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(generatedPolicy?.content || "");
  const [saving, setSaving] = useState(false);

  if (!generatedPolicy) {
    return null;
  }

  const handleDownload = () => {
    const blob = new Blob([generatedPolicy.content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${generatedPolicy.title.replace(/[^a-z0-9]/gi, "_")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRegenerate = async () => {
    if (!confirm("Are you sure you want to regenerate this policy? Your current draft will be lost.")) {
      return;
    }

    setCurrentStep("notes");
  };

  const handleSave = async () => {
    if (!selectedPolicyType) return;

    setSaving(true);
    setError(null);

    try {
      const contentToSave = isEditing ? editedContent : generatedPolicy.content;

      const response = await policyApi.saveGeneratedPolicy(
        generatedPolicy.title,
        contentToSave,
        generatedPolicy.sections,
        generatedPolicy.metadata,
        selectedPolicyType
      );

      // Show success state
      setCurrentStep("saved");

      // Reset after a delay
      setTimeout(() => {
        reset();
      }, 3000);
    } catch (err) {
      console.error("Failed to save policy:", err);
      setError(err instanceof Error ? err.message : "Failed to save policy");
    } finally {
      setSaving(false);
    }
  };

  const contentToDisplay = isEditing ? editedContent : generatedPolicy.content;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header card */}
      <Card className="border-2 border-yellow-200/50 shadow-dual-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">{generatedPolicy.title}</CardTitle>
              <CardDescription className="text-base mt-2">
                Generated {selectedPolicyTypeName} • Version {generatedPolicy.version}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setIsEditing(!isEditing)}>
                <Edit2 className="mr-2 h-4 w-4" />
                {isEditing ? "Preview" : "Edit"}
              </Button>
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="mr-2 h-4 w-4" />
                Download
              </Button>
              <Button variant="outline" size="sm" onClick={handleRegenerate} disabled={saving}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Regenerate
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Content card */}
      <Card>
        <CardContent className="pt-6">
          {isEditing ? (
            <Textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="min-h-[600px] font-mono text-sm border-gray-300 focus:border-yellow-400 focus:ring-yellow-400"
            />
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{contentToDisplay}</ReactMarkdown>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Metadata card */}
      <Card className="border-gray-200">
        <CardHeader>
          <CardTitle className="text-lg">Policy Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Policy Type:</span>
              <p className="font-medium text-gray-900">{selectedPolicyTypeName}</p>
            </div>
            <div>
              <span className="text-gray-500">Version:</span>
              <p className="font-medium text-gray-900">{generatedPolicy.version}</p>
            </div>
            <div>
              <span className="text-gray-500">Sections:</span>
              <p className="font-medium text-gray-900">{generatedPolicy.sections.length}</p>
            </div>
            <div>
              <span className="text-gray-500">Generation Method:</span>
              <p className="font-medium text-gray-900">
                {generatedPolicy.metadata.generation_method === "llm_questionnaire" ? "AI Questionnaire" : "Other"}
              </p>
            </div>
            {generatedPolicy.metadata.question_count && (
              <div>
                <span className="text-gray-500">Questions Answered:</span>
                <p className="font-medium text-gray-900">{generatedPolicy.metadata.question_count}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Save button */}
      <Card className="border-2 border-green-200/50 bg-green-50/30">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-start gap-3">
              <FileText className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Ready to save?</h4>
                <p className="text-sm text-gray-600">
                  This policy will be saved to your policy library and automatically added to the knowledge base
                  for contract analysis.
                </p>
              </div>
            </div>
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-gradient-to-r from-green-500 to-green-600 text-white hover:from-green-600 hover:to-green-700 shadow-dual-sm"
            >
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Policy
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
