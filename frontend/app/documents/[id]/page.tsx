"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { documentApi } from "@/lib/api";
import type { Document } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowLeft,
  Save,
  Check,
  Loader2,
  Download,
  Eye,
  Edit3,
  GitBranch,
  Users,
} from "lucide-react";
import {
  SuperDocEditor,
  type SuperDocEditorRef,
  type SuperDocInstance,
} from "@/components/editor/SuperDocEditor";
import { useAuth } from "@/contexts/AuthContext";
import { CollaboratorList } from "@/components/documents/CollaboratorList";
import { InviteCollaboratorModal } from "@/components/documents/InviteCollaboratorModal";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type SaveStatus = "idle" | "saving" | "saved" | "error";
type EditorMode = "editing" | "viewing" | "suggesting";

export default function DocumentEditorPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const documentId = params.id as string;

  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [documentFile, setDocumentFile] = useState<File | Blob | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [editorReady, setEditorReady] = useState(false);
  const [editorMode, setEditorMode] = useState<EditorMode>("editing");
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");
  const [collaboratorStates, setCollaboratorStates] = useState<any[]>([]);
  const [collaborationEnabled, setCollaborationEnabled] = useState(false);

  // Track if content has changed since last save
  const [isDirty, setIsDirty] = useState(false);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const editorRef = useRef<SuperDocEditorRef>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadDocument();
  }, [documentId]);

  // Auto-save every 30 seconds if dirty
  useEffect(() => {
    if (isDirty && saveStatus !== "saving" && editorReady) {
      saveTimeoutRef.current = setTimeout(() => {
        handleSave();
      }, 30000); // 30 seconds

      return () => {
        if (saveTimeoutRef.current) {
          clearTimeout(saveTimeoutRef.current);
        }
      };
    }
  }, [isDirty, editorReady]);

  const loadDocument = async () => {
    try {
      setLoading(true);
      const doc = await documentApi.getDocument(documentId);
      setDocument(doc);

      // Check if collaboration state exists (only enable collab if state exists)
      const hasCollabState = await documentApi.hasCollaborationState(documentId);
      setCollaborationEnabled(hasCollabState);
      console.log(
        "[Document Load] Collaboration state exists:",
        hasCollabState
      );

      // Check if this document has an original DOCX file
      if (doc.original_file_path) {
        console.log(
          "[Document Load] Loading DOCX file from:",
          doc.original_file_path
        );
        // Fetch the original DOCX file
        try {
          const blob = await documentApi.downloadOriginal(documentId);
          // The API already returns a Blob, no need to wrap it
          setDocumentFile(blob);
          console.log(
            "[Document Load] DOCX file loaded, size:",
            blob.size,
            "type:",
            blob.type
          );
        } catch (downloadError) {
          console.error("Failed to download DOCX file:", downloadError);
          // Create an empty document if download fails
          setDocumentFile(null);
        }
      } else {
        console.log(
          "[Document Load] No DOCX file found, starting with empty editor"
        );
        setDocumentFile(null);
      }
    } catch (error) {
      console.error("Failed to load document:", error);
      alert("Failed to load document. You may not have access.");
      router.push("/documents");
    } finally {
      setLoading(false);
    }
  };

  const handleEditorReady = useCallback((instance: SuperDocInstance) => {
    console.log("[SuperDoc] Editor ready");
    setEditorReady(true);
  }, []);

  const handleEditorChange = useCallback(() => {
    setIsDirty(true);
    setSaveStatus("idle");
  }, []);

  const handleConnectionStatusChange = useCallback((status: "connecting" | "connected" | "disconnected") => {
    setConnectionStatus(status);
    console.log("[Collaboration] Connection status:", status);
  }, []);

  const handleAwarenessUpdate = useCallback((states: any[]) => {
    setCollaboratorStates(states);
    console.log("[Collaboration] Awareness update:", states.length, "users");
  }, []);

  const handleModeChange = (mode: EditorMode) => {
    setEditorMode(mode);
    if (editorRef.current) {
      editorRef.current.setMode(mode);
    }
  };

  const handleEnableCollaboration = async () => {
    if (collaborationEnabled) return;

    try {
      // Enable collaboration by creating the Y.js state marker
      await documentApi.enableCollaboration(documentId);

      // Reload to connect with collaboration enabled
      alert("Collaboration enabled! The page will reload to connect to the collaboration server.");
      window.location.reload();
    } catch (error) {
      console.error("Failed to enable collaboration:", error);
      alert("Failed to enable collaboration. Please try again.");
    }
  };

  const handleSave = async () => {
    if (!isDirty || saveStatus === "saving" || !editorRef.current) return;

    try {
      setSaveStatus("saving");

      // Export document as DOCX blob
      const blob = await editorRef.current.export({ isFinalDoc: false });

      if (!blob) {
        throw new Error("Failed to export document");
      }

      // Create FormData to upload the DOCX file
      const formData = new FormData();
      formData.append("file", blob, `${document?.title || "document"}.docx`);

      // Update the document with the new DOCX content
      await documentApi.updateDocumentContent(documentId, formData);

      setIsDirty(false);
      setSaveStatus("saved");
      setLastSaved(new Date());

      // Reset to idle after 2 seconds
      setTimeout(() => {
        setSaveStatus("idle");
      }, 2000);
    } catch (error) {
      console.error("Failed to save document:", error);
      setSaveStatus("error");
      setTimeout(() => {
        setSaveStatus("idle");
      }, 3000);
    }
  };

  const handleExportDocx = async () => {
    if (!editorRef.current) return;

    try {
      const blob = await editorRef.current.export({ isFinalDoc: true });
      if (!blob) {
        throw new Error("Failed to export document");
      }

      // Create download link
      const url = URL.createObjectURL(blob);
      const a = window.document.createElement("a");
      a.href = url;
      a.download = `${document?.title || "document"}.docx`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to export document:", error);
      alert("Failed to export document");
    }
  };

  const getSaveStatusBadge = () => {
    switch (saveStatus) {
      case "saving":
        return (
          <Badge variant="secondary" className="gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            Saving...
          </Badge>
        );
      case "saved":
        return (
          <Badge variant="default" className="gap-1 bg-green-600">
            <Check className="h-3 w-3" />
            Saved
          </Badge>
        );
      case "error":
        return (
          <Badge variant="destructive" className="gap-1">
            Error saving
          </Badge>
        );
      default:
        if (lastSaved) {
          const now = new Date();
          const diffMs = now.getTime() - lastSaved.getTime();
          const diffMins = Math.floor(diffMs / 60000);

          if (diffMins < 1) {
            return (
              <Badge variant="outline" className="gap-1">
                Saved just now
              </Badge>
            );
          } else if (diffMins < 60) {
            return (
              <Badge variant="outline" className="gap-1">
                Saved {diffMins}m ago
              </Badge>
            );
          } else {
            return (
              <Badge variant="outline" className="gap-1">
                Saved at {lastSaved.toLocaleTimeString()}
              </Badge>
            );
          }
        }
        return null;
    }
  };

  const getModeIcon = (mode: EditorMode) => {
    switch (mode) {
      case "editing":
        return <Edit3 className="h-4 w-4" />;
      case "viewing":
        return <Eye className="h-4 w-4" />;
      case "suggesting":
        return <GitBranch className="h-4 w-4" />;
    }
  };

  const getConnectionStatusBadge = () => {
    if (!collaborationEnabled) {
      return (
        <Badge variant="outline" className="gap-1 text-blue-500">
          <div className="h-2 w-2 rounded-full bg-blue-400" />
          Local
        </Badge>
      );
    }

    switch (connectionStatus) {
      case "connecting":
        return (
          <Badge variant="secondary" className="gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            Connecting...
          </Badge>
        );
      case "connected":
        return (
          <Badge variant="default" className="gap-1 bg-green-600">
            <div className="h-2 w-2 rounded-full bg-white" />
            Live
          </Badge>
        );
      case "disconnected":
        return (
          <Badge variant="outline" className="gap-1 text-gray-500">
            <div className="h-2 w-2 rounded-full bg-gray-400" />
            Offline
          </Badge>
        );
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-gray-50">
        <div className="bg-white border-b p-4">
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="flex-1 p-8">
          <Skeleton className="h-full w-full" />
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Document not found
          </h2>
          <Button onClick={() => router.push("/documents")}>
            Back to Documents
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100 overflow-hidden">
      {/* Fixed Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm z-20">
        {/* Top bar with document info and actions */}
        <div className="flex items-center justify-between px-4 py-2">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/documents")}
              className="gap-1"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                {document.title}
              </h1>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Badge variant="secondary" className="text-xs">
                  {document.status}
                </Badge>
                {document.import_source && (
                  <span>
                    •{" "}
                    {document.import_source === "ai_redlined"
                      ? "AI Analysis"
                      : "Original"}
                  </span>
                )}
                <span>
                  • Updated {new Date(document.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {getConnectionStatusBadge()}
            {getSaveStatusBadge()}

            {/* Enable Collaboration Button (only show in local mode) */}
            {!collaborationEnabled && editorReady && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleEnableCollaboration}
                className="gap-1"
              >
                <Users className="h-4 w-4" />
                Enable Collab
              </Button>
            )}

            {/* Mode Selector */}
            <Select value={editorMode} onValueChange={(v) => handleModeChange(v as EditorMode)}>
              <SelectTrigger className="w-[140px]">
                <div className="flex items-center gap-2">
                  {getModeIcon(editorMode)}
                  <SelectValue />
                </div>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="editing">
                  <div className="flex items-center gap-2">
                    <Edit3 className="h-4 w-4" />
                    Editing
                  </div>
                </SelectItem>
                <SelectItem value="suggesting">
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-4 w-4" />
                    Suggesting
                  </div>
                </SelectItem>
                <SelectItem value="viewing">
                  <div className="flex items-center gap-2">
                    <Eye className="h-4 w-4" />
                    Viewing
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>

            <CollaboratorList
              documentId={documentId}
              onInviteClick={() => setShowInviteModal(true)}
            />

            <Button
              variant="outline"
              size="sm"
              onClick={handleExportDocx}
              disabled={!editorReady}
              className="gap-1"
            >
              <Download className="h-4 w-4" />
              Export
            </Button>

            <Button
              size="sm"
              onClick={handleSave}
              disabled={
                !isDirty ||
                saveStatus === "saving" ||
                !editorReady ||
                editorMode === "viewing"
              }
              className="gap-1"
            >
              <Save className="h-4 w-4" />
              Save
            </Button>
          </div>
        </div>

        {/* SuperDoc Toolbar Container */}
        <div
          ref={toolbarRef}
          id="superdoc-toolbar"
          className="border-t border-gray-100 bg-gray-50 min-h-[44px]"
        />
      </header>

      {/* Main Editor Area */}
      <main className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto bg-gray-100">
          <div className="max-w-5xl mx-auto py-8 px-4">
            {/* Document Canvas */}
            <div className="bg-white rounded-sm shadow-lg">
              {!documentFile ? (
                <div className="flex items-center justify-center min-h-[600px] bg-gray-50">
                  <div className="text-center p-8">
                    <div className="text-gray-400 mb-4">
                      <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No DOCX File Available
                    </h3>
                    <p className="text-sm text-gray-500 mb-4">
                      This document doesn't have a DOCX file attached.
                      <br />
                      Import a DOCX file from the Documents page to edit it here.
                    </p>
                    <Button
                      variant="outline"
                      onClick={() => router.push("/documents")}
                    >
                      Go to Documents
                    </Button>
                  </div>
                </div>
              ) : (
                <SuperDocEditor
                  ref={editorRef}
                  documentFile={documentFile}
                  user={
                    user
                      ? {
                          name: user.email,
                          email: user.email,
                        }
                      : undefined
                  }
                  onReady={handleEditorReady}
                  onChange={handleEditorChange}
                  onConnectionStatusChange={handleConnectionStatusChange}
                  onAwarenessUpdate={handleAwarenessUpdate}
                  height="auto"
                  className="min-h-[800px]"
                  enableToolbar={true}
                  toolbarSelector="#superdoc-toolbar"
                  initialMode={editorMode}
                  collaboration={
                    user && collaborationEnabled
                      ? {
                          enabled: true,
                          documentId: documentId,
                          userId: user.id,
                        }
                      : undefined
                  }
                />
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Auto-save indicator */}
      {isDirty && editorReady && editorMode !== "viewing" && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-sm px-4 py-2 rounded-full shadow-lg">
          Auto-save in 30 seconds
        </div>
      )}

      {/* Invite Collaborator Modal */}
      <InviteCollaboratorModal
        open={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        onSuccess={() => {
          setShowInviteModal(false);
          // Collaborator list will auto-refresh
        }}
        documentId={documentId}
        documentTitle={document?.title || "Untitled Document"}
      />
    </div>
  );
}
