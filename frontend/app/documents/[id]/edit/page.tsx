"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Save,
  ArrowLeft,
  CheckCircle,
  XCircle,
  Send,
  Users,
  FileSignature,
  AlertCircle
} from "lucide-react";
import { SuperDocEditor, SuperDocEditorRef } from "@/components/editor/SuperDocEditor";
import { API_BASE_URL } from "@/lib/api";
import { toast } from "sonner";

interface DocumentData {
  id: string;
  filename: string;
  status: string;
  approval_status?: string;
  signature_status?: string;
  version_number?: number;
  is_locked?: boolean;
  lock_reason?: string;
  all_parties_approved?: boolean;
  signatures_required?: number;
  signatures_completed?: number;
}

export default function DocumentEditPage() {
  const params = useParams();
  const router = useRouter();
  const editorRef = useRef<SuperDocEditorRef>(null);

  const documentId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [document, setDocument] = useState<DocumentData | null>(null);
  const [documentBlob, setDocumentBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showApprovalButtons, setShowApprovalButtons] = useState(false);
  const [showSignatureButtons, setShowSignatureButtons] = useState(false);

  useEffect(() => {
    fetchDocument();
  }, [documentId]);

  const fetchDocument = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch document metadata
      const metaResponse = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
        credentials: "include",
      });

      if (!metaResponse.ok) {
        throw new Error("Failed to fetch document");
      }

      const docData = await metaResponse.json();
      setDocument(docData);

      // Check if document is locked
      if (docData.is_locked) {
        setError(`Document is locked: ${docData.lock_reason}`);
        return;
      }

      // Fetch document content
      const contentResponse = await fetch(
        `${API_BASE_URL}/api/documents/${documentId}/latest-version`,
        {
          credentials: "include",
        }
      );

      if (!contentResponse.ok) {
        throw new Error("Failed to fetch document content");
      }

      const blob = await contentResponse.blob();
      setDocumentBlob(blob);

      // Determine which buttons to show
      setShowApprovalButtons(
        docData.approval_status !== "approved" &&
        !docData.all_parties_approved
      );

      setShowSignatureButtons(
        docData.approval_status === "approved" ||
        docData.all_parties_approved
      );

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load document");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editorRef.current) return;

    try {
      setSaving(true);
      const blob = await editorRef.current.export();

      if (!blob) {
        throw new Error("Failed to export document");
      }

      const formData = new FormData();
      formData.append("file", blob, document?.filename || "document.docx");
      formData.append("summary", "Edited in document editor");

      const response = await fetch(
        `${API_BASE_URL}/api/documents/${documentId}/save-version`,
        {
          method: "POST",
          credentials: "include",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Failed to save document");
      }

      const result = await response.json();

      toast.success("Document saved", {
        description: `Version ${result.version} saved successfully`,
      });

      // Update local document data
      if (document) {
        setDocument({
          ...document,
          version_number: result.version,
        });
      }

    } catch (err) {
      toast.error("Save failed", {
        description: err instanceof Error ? err.message : "Failed to save document",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/documents/${documentId}/approve`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to approve document");
      }

      toast.success("Document approved", {
        description: "Your approval has been recorded",
      });

      // Refresh document status
      fetchDocument();

    } catch (err) {
      toast.error("Approval failed", {
        description: err instanceof Error ? err.message : "Failed to approve document",
      });
    }
  };

  const handleReject = async () => {
    // TODO: Show modal for rejection comments
    const comments = prompt("Please provide rejection comments:");

    if (!comments) return;

    try {
      const formData = new FormData();
      formData.append("comments", comments);

      const response = await fetch(
        `${API_BASE_URL}/api/documents/${documentId}/reject`,
        {
          method: "POST",
          credentials: "include",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Failed to reject document");
      }

      toast.success("Document rejected", {
        description: "Your rejection has been recorded",
      });

      // Refresh document status
      fetchDocument();

    } catch (err) {
      toast.error("Rejection failed", {
        description: err instanceof Error ? err.message : "Failed to reject document",
      });
    }
  };

  const handleRequestSignatures = () => {
    // Navigate to signature request page
    router.push(`/documents/${documentId}/signatures`);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button
          className="mt-4"
          onClick={() => router.push("/results")}
          variant="outline"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Results
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/results")}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-xl font-semibold">
                  {document?.filename || "Document"}
                </h1>
                <div className="flex gap-2 mt-1">
                  <Badge variant="outline">
                    Version {document?.version_number || 1}
                  </Badge>
                  {document?.approval_status && (
                    <Badge
                      variant={
                        document.approval_status === "approved"
                          ? "default"
                          : document.approval_status === "rejected"
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {document.approval_status}
                    </Badge>
                  )}
                  {document?.signature_status && (
                    <Badge variant="secondary">
                      {document.signatures_completed || 0} of {document.signatures_required || 0} signed
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              {/* Save Button */}
              <Button
                onClick={handleSave}
                disabled={saving || document?.is_locked}
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? "Saving..." : "Save"}
              </Button>

              {/* Approval Buttons */}
              {showApprovalButtons && (
                <>
                  <Button
                    variant="outline"
                    onClick={handleApprove}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleReject}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </Button>
                </>
              )}

              {/* Signature Button */}
              {showSignatureButtons && (
                <Button
                  variant="default"
                  onClick={handleRequestSignatures}
                >
                  <FileSignature className="h-4 w-4 mr-2" />
                  Request Signatures
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Editor */}
      <div className="container mx-auto px-4 py-4">
        <Card className="p-4">
          {documentBlob ? (
            <SuperDocEditor
              ref={editorRef}
              documentFile={documentBlob}
              height="700px"
              initialMode={document?.is_locked ? "viewing" : "editing"}
              user={{
                name: "Current User",
                email: "user@example.com"
              }}
            />
          ) : (
            <div className="h-96 flex items-center justify-center text-gray-500">
              No document content available
            </div>
          )}
        </Card>
      </div>

      {/* Status Sidebar (placeholder for future implementation) */}
      {/* This would show real-time approval status and signatures */}
    </div>
  );
}