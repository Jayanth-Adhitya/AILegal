"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, FileText, Edit, Trash2, CheckCircle2, Clock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Policy } from "@/lib/types";
import { policyApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { PolicyChatbot } from "@/components/policies/policy-chatbot";

interface PolicyDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function PolicyDetailPage({ params }: PolicyDetailPageProps) {
  const resolvedParams = use(params);
  const router = useRouter();
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"policy" | "chat">("policy");

  useEffect(() => {
    loadPolicy();
  }, [resolvedParams.id]);

  const loadPolicy = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await policyApi.getPolicy(resolvedParams.id);
      setPolicy(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load policy");
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      active: { color: "bg-green-100 text-green-800", icon: CheckCircle2 },
      draft: { color: "bg-yellow-100 text-yellow-800", icon: Clock },
      archived: { color: "bg-gray-100 text-gray-800", icon: AlertCircle },
    };
    const variant = variants[status as keyof typeof variants] || variants.active;
    const Icon = variant.icon;

    return (
      <Badge variant="secondary" className={variant.color}>
        <Icon className="mr-1 h-3 w-3" />
        {status}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="h-full p-8">
        <div className="mx-auto max-w-5xl space-y-6">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  if (error || !policy) {
    return (
      <div className="h-full p-8">
        <div className="mx-auto max-w-5xl">
          <Alert variant="destructive">
            <AlertDescription>{error || "Policy not found"}</AlertDescription>
          </Alert>
          <Button onClick={() => router.push("/policies")} className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Policies
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full p-8">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <Button
              variant="ghost"
              onClick={() => router.push("/policies")}
              className="mb-4"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Policies
            </Button>
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{policy.title}</h1>
                <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
                  {policy.policy_number && (
                    <span>Policy #{policy.policy_number}</span>
                  )}
                  <span>Version {policy.version}</span>
                  {policy.effective_date && (
                    <span>Effective {formatDate(policy.effective_date)}</span>
                  )}
                  {getStatusBadge(policy.status)}
                </div>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          </div>
        </div>

        {/* View Switcher */}
        <div className="mb-4 flex items-center gap-2 border-b pb-4">
          <button
            onClick={() => setView("policy")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              view === "policy"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Policy View
          </button>
          <button
            onClick={() => setView("chat")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              view === "chat"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Chat View
          </button>
        </div>

        {/* Conditional Rendering based on view */}
        {view === "policy" ? (
        <Tabs defaultValue="sections" className="w-full">
          <TabsList>
            <TabsTrigger value="sections">
              Sections {policy.sections && `(${policy.sections.length})`}
            </TabsTrigger>
            <TabsTrigger value="full-text">Full Text</TabsTrigger>
            <TabsTrigger value="metadata">Metadata</TabsTrigger>
            {policy.versions && policy.versions.length > 0 && (
              <TabsTrigger value="history">
                Version History ({policy.versions.length})
              </TabsTrigger>
            )}
          </TabsList>

          {/* Sections Tab */}
          <TabsContent value="sections" className="space-y-4">
            {policy.sections && policy.sections.length > 0 ? (
              policy.sections.map((section, index) => (
                <Card key={section.id}>
                  <CardHeader>
                    <CardTitle className="text-lg">
                      {section.section_number && `${section.section_number}. `}
                      {section.section_title || `Section ${index + 1}`}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700">
                      {section.section_content}
                    </pre>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card>
                <CardContent className="p-12 text-center">
                  <p className="text-gray-500">No sections found in this policy</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Full Text Tab */}
          <TabsContent value="full-text">
            <Card>
              <CardContent className="p-6">
                <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700">
                  {policy.full_text || "No full text available"}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Metadata Tab */}
          <TabsContent value="metadata">
            <Card>
              <CardContent className="p-6">
                <dl className="grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Policy ID</dt>
                    <dd className="mt-1 text-sm text-gray-900">{policy.id}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Original Filename</dt>
                    <dd className="mt-1 text-sm text-gray-900">{policy.original_filename}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">File Type</dt>
                    <dd className="mt-1 text-sm text-gray-900">{policy.file_type.toUpperCase()}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">File Size</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {policy.file_size ? `${(policy.file_size / 1024).toFixed(2)} KB` : "N/A"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Created At</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatDate(policy.created_at)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatDate(policy.updated_at)}</dd>
                  </div>
                  {policy.summary && (
                    <div className="col-span-2">
                      <dt className="text-sm font-medium text-gray-500">Summary</dt>
                      <dd className="mt-1 text-sm text-gray-900">{policy.summary}</dd>
                    </div>
                  )}
                </dl>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Version History Tab */}
          {policy.versions && policy.versions.length > 0 && (
            <TabsContent value="history">
              <div className="space-y-4">
                {policy.versions.map((version) => (
                  <Card key={version.id}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg">Version {version.version_number}</CardTitle>
                          <CardDescription>
                            {formatDate(version.created_at)}
                            {version.changed_by && ` by ${version.changed_by.email}`}
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    {version.change_description && (
                      <CardContent>
                        <p className="text-sm text-gray-700">{version.change_description}</p>
                      </CardContent>
                    )}
                  </Card>
                ))}
              </div>
            </TabsContent>
          )}
        </Tabs>
        ) : (
          <PolicyChatbot policy={policy} />
        )}
      </div>
    </div>
  );
}
