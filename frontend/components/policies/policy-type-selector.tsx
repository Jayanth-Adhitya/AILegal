"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, FileText, Sparkles } from "lucide-react";
import { useDraftPolicy } from "@/contexts/DraftPolicyContext";
import { policyApi } from "@/lib/api";

interface PolicyType {
  id: string;
  name: string;
  description: string;
}

interface PolicyTypesResponse {
  status: string;
  policy_types: Record<string, PolicyType[]>;
  total_count: number;
}

export function PolicyTypeSelector() {
  const { selectPolicyType, setQuestions, setLoading, setError } = useDraftPolicy();
  const [policyTypes, setPolicyTypes] = useState<Record<string, PolicyType[]>>({});
  const [selectedType, setSelectedType] = useState<string>("");
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [generatingQuestions, setGeneratingQuestions] = useState(false);

  // Load policy types on mount
  useEffect(() => {
    loadPolicyTypes();
  }, []);

  const loadPolicyTypes = async () => {
    setLoadingTypes(true);
    try {
      const response = await policyApi.getPolicyTypes();
      setPolicyTypes(response.policy_types);
    } catch (err) {
      console.error("Failed to load policy types:", err);
      setError(err instanceof Error ? err.message : "Failed to load policy types");
    } finally {
      setLoadingTypes(false);
    }
  };

  const handleSelectAndContinue = async () => {
    if (!selectedType) return;

    // Find the selected policy type details
    let selectedTypeName = "";
    for (const category in policyTypes) {
      const found = policyTypes[category].find((pt) => pt.id === selectedType);
      if (found) {
        selectedTypeName = found.name;
        break;
      }
    }

    setGeneratingQuestions(true);
    setLoading(true);
    setError(null);

    try {
      // Generate questions for this policy type
      const response = await policyApi.generateQuestions(selectedType);

      // Update context with questions and policy type
      setQuestions(response.questions);
      selectPolicyType(selectedType, selectedTypeName);
    } catch (err) {
      console.error("Failed to generate questions:", err);
      setError(err instanceof Error ? err.message : "Failed to generate questions");
    } finally {
      setGeneratingQuestions(false);
      setLoading(false);
    }
  };

  if (loadingTypes) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-yellow-500" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <Card className="border-2 border-yellow-200/50 shadow-dual-sm">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-yellow-400 to-yellow-500 rounded-lg">
              <Sparkles className="h-6 w-6 text-gray-900" />
            </div>
            <div>
              <CardTitle className="text-2xl">Select Policy Type</CardTitle>
              <CardDescription className="text-base mt-1">
                Choose the type of policy you want to create
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              Policy Type <span className="text-red-500">*</span>
            </label>
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-full border-gray-300 focus:border-yellow-400 focus:ring-yellow-400">
                <SelectValue placeholder="Select a policy type..." />
              </SelectTrigger>
              <SelectContent className="max-h-[400px]">
                {Object.entries(policyTypes).map(([category, types]) => (
                  <SelectGroup key={category}>
                    <SelectLabel className="font-semibold text-gray-900">{category}</SelectLabel>
                    {types.map((type) => (
                      <SelectItem key={type.id} value={type.id}>
                        <div className="flex flex-col py-1">
                          <span className="font-medium">{type.name}</span>
                          <span className="text-xs text-gray-500">{type.description}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectGroup>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedType && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <FileText className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-gray-700">
                  <p className="font-medium mb-1">What happens next?</p>
                  <p>
                    Cirilla AI will generate 8-12 questions tailored to this policy type.
                    Answer them to help create a comprehensive, professional policy document.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button
              onClick={handleSelectAndContinue}
              disabled={!selectedType || generatingQuestions}
              className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 hover:from-yellow-500 hover:to-yellow-600 shadow-dual-sm"
            >
              {generatingQuestions ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating Questions...
                </>
              ) : (
                "Continue"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Info card */}
      <Card className="mt-6 border-gray-200">
        <CardContent className="pt-6">
          <h3 className="font-semibold text-gray-900 mb-3">Available Policy Categories</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.keys(policyTypes).map((category) => (
              <div key={category} className="flex items-center gap-2 text-sm text-gray-600">
                <div className="h-2 w-2 rounded-full bg-yellow-400"></div>
                <span>{category}</span>
                <span className="text-gray-400">({policyTypes[category].length})</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
