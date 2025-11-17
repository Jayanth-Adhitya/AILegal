/**
 * Lexical plugin for Yjs-based real-time collaboration.
 *
 * This plugin binds a Yjs document to the Lexical editor, enabling:
 * - Real-time synchronization across multiple clients
 * - Offline editing with local persistence
 * - User awareness (cursors and presence)
 */

"use client";

import { useEffect, useState } from "react";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import type { YjsProviders } from "@/lib/editor/yjs-provider";
import * as Y from "yjs";

export interface CollaborationPluginProps {
  providers: YjsProviders | null;
  shouldBootstrap: boolean;
}

export function CollaborationPlugin({
  providers,
  shouldBootstrap,
}: CollaborationPluginProps) {
  const [editor] = useLexicalComposerContext();
  const [synced, setSynced] = useState(false);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (!providers) return;

    const { doc, provider } = providers;

    // Get or create shared text for storing editor state JSON
    const sharedText = doc.getText("editorState");

    // Initialize Yjs with current editor state if it's empty
    if (!initialized) {
      const existingContent = sharedText.toString();

      if (!existingContent || existingContent.trim() === "") {
        // Yjs is empty - seed it with current editor state
        const currentState = editor.getEditorState();
        const json = currentState.toJSON();
        const content = JSON.stringify(json);

        doc.transact(() => {
          sharedText.insert(0, content);
        });

        console.log("[CollaborationPlugin] Initialized Yjs with current editor state");
      }

      setInitialized(true);
    }

    // Wait for initial sync
    const handleSync = (isSynced: boolean) => {
      if (isSynced && !synced) {
        console.log("[CollaborationPlugin] Initial sync complete");
        setSynced(true);

        // Load state from Yjs if it exists and differs from current
        const content = sharedText.toString();
        if (content && content.trim() !== "") {
          try {
            // Validate JSON before parsing
            JSON.parse(content);

            const currentState = JSON.stringify(editor.getEditorState().toJSON());

            // Only update if Yjs content differs
            if (content !== currentState) {
              editor.update(
                () => {
                  const editorState = editor.parseEditorState(content);
                  editor.setEditorState(editorState);
                },
                { tag: "collaboration" }
              );
              console.log("[CollaborationPlugin] Loaded remote state from Yjs");
            }
          } catch (e) {
            console.error("[CollaborationPlugin] Failed to parse remote state - clearing corrupted data:", e);

            // Clear corrupted Yjs content and reinitialize with current editor state
            doc.transact(() => {
              sharedText.delete(0, sharedText.length);
              const currentState = editor.getEditorState();
              const json = currentState.toJSON();
              const validContent = JSON.stringify(json);
              sharedText.insert(0, validContent);
            });

            console.log("[CollaborationPlugin] Reinitialized Yjs with current editor state after clearing corruption");
          }
        }
      }
    };

    provider.on("sync", handleSync);

    // Sync Yjs changes to Lexical
    const handleYjsUpdate = () => {
      if (!synced) return; // Wait for initial sync

      const content = sharedText.toString();
      if (!content || content.trim() === "") return;

      try {
        // Validate JSON before parsing
        JSON.parse(content);

        const currentState = JSON.stringify(editor.getEditorState().toJSON());

        // Only update if content actually changed
        if (content !== currentState) {
          editor.update(
            () => {
              const editorState = editor.parseEditorState(content);
              editor.setEditorState(editorState);
            },
            { tag: "collaboration" }
          );
          console.log("[CollaborationPlugin] Applied remote update");
        }
      } catch (e) {
        console.error("[CollaborationPlugin] Failed to apply remote update - ignoring corrupted data:", e);
        // Don't try to fix here - let the next valid update overwrite
      }
    };

    sharedText.observe(handleYjsUpdate);

    // Sync Lexical changes to Yjs
    const removeUpdateListener = editor.registerUpdateListener(
      ({ editorState, tags }) => {
        // Skip if this update came from Yjs or is historic
        if (tags.has("collaboration") || tags.has("historic")) {
          return;
        }

        // Broadcast the change via Yjs
        doc.transact(() => {
          const json = editorState.toJSON();
          const content = JSON.stringify(json);

          // Only update if content changed
          const currentYjsContent = sharedText.toString();
          if (currentYjsContent !== content) {
            sharedText.delete(0, sharedText.length);
            sharedText.insert(0, content);
            console.log("[CollaborationPlugin] Broadcasted local change");
          }
        });
      }
    );

    return () => {
      provider.off("sync", handleSync);
      sharedText.unobserve(handleYjsUpdate);
      removeUpdateListener();
    };
  }, [editor, providers, shouldBootstrap, synced, initialized]);

  return null;
}
