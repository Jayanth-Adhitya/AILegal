"use client";

import {
  useEffect,
  useRef,
  forwardRef,
  useImperativeHandle,
  useState,
} from "react";

// Import custom overrides
import "@/styles/superdoc-overrides.css";

// Define types for SuperDoc
interface SuperDocUser {
  name: string;
  email: string;
  color?: string;
}

interface ExportOptions {
  isFinalDoc?: boolean;
}

interface SuperDocInstance {
  export: (options?: ExportOptions) => Promise<Blob>;
  setDocumentMode: (mode: "editing" | "viewing" | "suggesting") => void;
  getHTML: () => string[];
  destroy?: () => void;
}

export interface SuperDocEditorRef {
  export: (options?: ExportOptions) => Promise<Blob | null>;
  setMode: (mode: "editing" | "viewing" | "suggesting") => void;
  getHTML: () => string[];
  getInstance: () => SuperDocInstance | null;
}

interface CollaborationConfig {
  enabled: boolean;
  documentId: string;
  userId: string;
  serverUrl?: string; // WebSocket URL, defaults to ws://localhost:8080
}

interface SuperDocEditorProps {
  documentFile?: File | Blob | null;
  documentUrl?: string;
  user?: SuperDocUser;
  onReady?: (instance: SuperDocInstance) => void;
  onChange?: () => void;
  onAwarenessUpdate?: (states: any[]) => void;
  onConnectionStatusChange?: (status: "connecting" | "connected" | "disconnected") => void;
  height?: string;
  className?: string;
  toolbarSelector?: string | HTMLElement;
  enableToolbar?: boolean;
  initialMode?: "editing" | "viewing" | "suggesting";
  collaboration?: CollaborationConfig;
}

// Direct export without dynamic wrapper - the parent page is already "use client"
export const SuperDocEditor = forwardRef<SuperDocEditorRef, SuperDocEditorProps>(
  (
    {
      documentFile,
      documentUrl,
      user,
      onReady,
      onChange,
      onAwarenessUpdate,
      onConnectionStatusChange,
      height = "700px",
      className = "",
      toolbarSelector,
      enableToolbar = true,
      initialMode = "editing",
      collaboration,
    },
    ref
  ) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const superdocRef = useRef<SuperDocInstance | null>(null);
    const providerRef = useRef<any>(null);
    const ydocRef = useRef<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isMounted, setIsMounted] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");

    // Ensure we only render on client
    useEffect(() => {
      setIsMounted(true);
    }, []);

    useImperativeHandle(ref, () => ({
      export: async (options?: ExportOptions) => {
        if (!superdocRef.current) return null;
        return superdocRef.current.export(options);
      },
      setMode: (mode: "editing" | "viewing" | "suggesting") => {
        superdocRef.current?.setDocumentMode(mode);
      },
      getHTML: () => {
        return superdocRef.current?.getHTML() || [];
      },
      getInstance: () => superdocRef.current,
    }));

    useEffect(() => {
      if (!isMounted) return;

      let mounted = true;
      let superdocInstance: any = null;
      let initializationStarted = false;

      const initSuperDoc = async () => {
        if (!containerRef.current) return;

        // Prevent double initialization
        if (initializationStarted) {
          console.log("[SuperDoc] Initialization already in progress, skipping...");
          return;
        }
        initializationStarted = true;

        // Don't initialize if we're expecting a document but don't have one yet
        if (!documentFile && !documentUrl) {
          console.log("[SuperDoc] No document provided, waiting...");
          setIsLoading(false);
          return;
        }

        // Check if SuperDoc is already initialized in this container
        if (superdocRef.current) {
          console.log("[SuperDoc] Already initialized, skipping...");
          setIsLoading(false);
          return;
        }

        try {
          setIsLoading(true);
          setError(null);

          console.log("[SuperDoc] Initializing with document:", documentFile ? `Blob (${documentFile.size} bytes)` : documentUrl);

          // Dynamically load SuperDoc CSS
          const existingStyle = window.document.querySelector('link[href*="superdoc"]');
          if (!existingStyle) {
            // Import CSS as module - use @ts-ignore for CSS import
            // @ts-ignore - CSS module import
            await import("@harbour-enterprises/superdoc/style.css");
          }

          // Dynamic import for SSR compatibility
          const SuperDocModule = await import("@harbour-enterprises/superdoc");
          const SuperDoc = SuperDocModule.SuperDoc;

          if (!SuperDoc) {
            throw new Error("SuperDoc class not found in module");
          }

          if (!mounted) return;

          // Wait a tick to ensure DOM is fully ready
          await new Promise(resolve => setTimeout(resolve, 100));

          if (!mounted || !containerRef.current) return;

          // Generate a unique ID for this container if it doesn't have one
          if (!containerRef.current.id) {
            containerRef.current.id = `superdoc-container-${Date.now()}`;
          }
          const containerId = `#${containerRef.current.id}`;

          // Setup collaboration if enabled
          let serverUrl: string = "";

          if (collaboration?.enabled && collaboration.documentId) {
            console.log("[SuperDoc] Setting up collaboration for document:", collaboration.documentId);
            setConnectionStatus("connecting");
            onConnectionStatusChange?.("connecting");

            // Determine SuperDoc collaboration WebSocket URL
            // The server runs on port 1234 and expects /collaboration/:documentId
            const wsProtocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
            const wsHost = collaboration.serverUrl ||
              (typeof window !== "undefined"
                ? `${wsProtocol}//${window.location.hostname}:1234`
                : "ws://localhost:1234");

            serverUrl = wsHost;
            console.log("[SuperDoc] Collaboration server URL:", serverUrl);
          }

          const config: Record<string, any> = {
            selector: containerId,
            documentMode: initialMode,
            user: user || {
              name: "Anonymous User",
              email: "anonymous@example.com",
            },
            onReady: (instance: SuperDocInstance) => {
              console.log("[SuperDoc] onReady called, instance:", instance);
              superdocRef.current = instance;
              setIsLoading(false);

              // If collaboration is enabled, mark as connected once ready
              // SuperDoc handles the actual WebSocket connection internally
              if (collaboration?.enabled) {
                setConnectionStatus("connected");
                onConnectionStatusChange?.("connected");
              }

              onReady?.(instance);
            },
            onError: (error: any) => {
              console.error("[SuperDoc] Error:", error);
              if (mounted) {
                setError(error?.message || "SuperDoc initialization failed");
                setIsLoading(false);
              }
            },
          };

          // Set document source using documents array (required for SuperDoc)
          // SuperDoc requires a documents array with document configuration
          const documentConfig: Record<string, any> = {
            id: collaboration?.documentId || `doc-${Date.now()}`,
            type: "docx",
          };

          if (documentFile) {
            documentConfig.data = documentFile;
          } else if (documentUrl) {
            documentConfig.url = documentUrl;
          } else {
            throw new Error("No document provided to SuperDoc");
          }

          // Add collaboration module config if enabled
          // Uses HocusPocus-compatible server for real-time Y.js synchronization
          if (collaboration?.enabled && serverUrl) {
            // Mark document as new file for collaboration initialization
            // This tells SuperDoc to initialize the Y.js meta map with the docx data
            documentConfig.isNewFile = true;

            config.modules = {
              collaboration: {
                url: serverUrl,
                token: collaboration.userId, // User ID is used as auth token
              },
            };
            console.log("[SuperDoc] Collaboration module enabled with HocusPocus server");
            console.log("[SuperDoc] Document marked as isNewFile for meta map initialization");
          }

          config.documents = [documentConfig];

          // Configure toolbar if enabled and selector element exists
          if (enableToolbar && toolbarSelector) {
            // SuperDoc expects a string CSS selector, not an HTML element
            if (typeof toolbarSelector === 'string') {
              const toolbarElement = window.document.querySelector(toolbarSelector);
              if (toolbarElement) {
                console.log("[SuperDoc] Toolbar element found:", toolbarSelector);
                config.toolbar = toolbarSelector;
              } else {
                console.warn("[SuperDoc] Toolbar selector not found:", toolbarSelector);
              }
            } else {
              // If HTMLElement was passed, try to get its ID
              const el = toolbarSelector as HTMLElement;
              if (el.id) {
                config.toolbar = `#${el.id}`;
              } else {
                console.warn("[SuperDoc] Toolbar element has no ID, toolbar will not be rendered");
              }
            }
          }

          // Initialize SuperDoc
          console.log("[SuperDoc] Creating instance with config:", {
            ...config,
            document: config.document ? "provided" : "none",
            toolbar: config.toolbar ? "provided" : "none"
          });

          superdocInstance = new SuperDoc(config as any);

          // If onReady doesn't fire within 10 seconds, mark as loaded anyway
          setTimeout(() => {
            if (mounted && isLoading) {
              console.warn("[SuperDoc] onReady timeout, marking as loaded");
              setIsLoading(false);
            }
          }, 10000);
        } catch (err) {
          console.error("Failed to initialize SuperDoc:", err);
          if (mounted) {
            setError(
              err instanceof Error ? err.message : "Failed to load editor"
            );
            setIsLoading(false);
          }
        }
      };

      // Add a small delay to avoid React Strict Mode race conditions
      const timeoutId = setTimeout(() => {
        initSuperDoc();
      }, 100);

      return () => {
        mounted = false;
        clearTimeout(timeoutId);
        console.log("[SuperDoc] Cleaning up...");

        // Clean up SuperDoc instance first (this should unmount Vue app)
        if (superdocInstance) {
          try {
            if (typeof superdocInstance.destroy === 'function') {
              superdocInstance.destroy();
            }
          } catch (e) {
            console.error("[SuperDoc] Error destroying instance:", e);
          }
          superdocInstance = null;
        }

        if (superdocRef.current?.destroy) {
          try {
            superdocRef.current.destroy();
          } catch (e) {
            console.error("[SuperDoc] Error destroying ref instance:", e);
          }
        }
        superdocRef.current = null;

        // Clean up provider
        if (providerRef.current) {
          try {
            providerRef.current.disconnect();
            providerRef.current.destroy();
          } catch (e) {
            console.error("[SuperDoc] Error cleaning up provider:", e);
          }
          providerRef.current = null;
        }

        // Clean up Y.js document
        if (ydocRef.current) {
          try {
            ydocRef.current.destroy();
          } catch (e) {
            console.error("[SuperDoc] Error cleaning up ydoc:", e);
          }
          ydocRef.current = null;
        }

        // Clear the container DOM to ensure clean remount
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
        }

        console.log("[SuperDoc] Cleanup complete");
      };
    // Only depend on primitive values to avoid infinite loops
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [
      documentFile,
      documentUrl,
      isMounted,
      initialMode,
      enableToolbar,
      toolbarSelector,
      // Use primitive values from objects instead of objects themselves
      user?.name,
      user?.email,
      collaboration?.enabled,
      collaboration?.documentId,
      collaboration?.userId,
    ]);

    // Show loading until mounted on client
    if (!isMounted) {
      return (
        <div className="flex items-center justify-center h-[700px] bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Loading editor...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div
          className={`flex items-center justify-center bg-red-50 border border-red-200 rounded-lg ${className}`}
          style={{ height }}
        >
          <div className="text-center p-4">
            <p className="text-red-600 font-medium mb-2">
              Failed to load editor
            </p>
            <p className="text-sm text-red-500">{error}</p>
          </div>
        </div>
      );
    }

    // Show message if no document is provided
    if (!documentFile && !documentUrl && !isLoading) {
      return (
        <div
          className={`flex items-center justify-center bg-gray-50 border border-gray-200 rounded-lg ${className}`}
          style={{ height }}
        >
          <div className="text-center p-4">
            <p className="text-gray-600 font-medium mb-2">
              No DOCX file available
            </p>
            <p className="text-sm text-gray-500">
              This document does not have a DOCX file. Please import a DOCX file to use the SuperDoc editor.
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className={`relative ${className}`} style={{ minHeight: height === "auto" ? "600px" : height }}>
        {isLoading && (
          <div
            className="absolute inset-0 flex items-center justify-center bg-gray-50 rounded-lg z-10"
          >
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
              <p className="text-sm text-gray-600">Loading SuperDoc editor...</p>
            </div>
          </div>
        )}
        <div
          ref={containerRef}
          className="superdoc-container bg-white"
          style={{
            minHeight: height === "auto" ? "600px" : height,
            width: "100%",
          }}
        />
      </div>
    );
  }
);

SuperDocEditor.displayName = "SuperDocEditor";

export type { SuperDocUser, SuperDocInstance, ExportOptions, CollaborationConfig };
