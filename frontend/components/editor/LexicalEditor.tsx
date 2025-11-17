"use client";

import { LexicalComposer } from "@lexical/react/LexicalComposer";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import { OnChangePlugin } from "@lexical/react/LexicalOnChangePlugin";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { HeadingNode, QuoteNode } from "@lexical/rich-text";
import { ListItemNode, ListNode } from "@lexical/list";
import { CodeNode } from "@lexical/code";
import { AutoLinkNode, LinkNode } from "@lexical/link";
import { TableNode, TableCellNode, TableRowNode } from "@lexical/table";
import { TablePlugin } from "@lexical/react/LexicalTablePlugin";
import { EditorState } from "lexical";
import { $generateNodesFromDOM } from "@lexical/html";
import { $getRoot } from "lexical";
import { useEffect } from "react";
import { EditorToolbar } from "./EditorToolbar";
import { CollaborationPlugin } from "./CollaborationPlugin";
import type { YjsProviders } from "@/lib/editor/yjs-provider";

interface LexicalEditorProps {
  initialContent?: string;
  onChange?: (content: string) => void;
  readOnly?: boolean;
  placeholder?: string;
  yjsProviders?: YjsProviders | null;
  enableCollaboration?: boolean;
}

const theme = {
  paragraph: "mb-2",
  heading: {
    h1: "text-3xl font-bold mb-4 mt-6",
    h2: "text-2xl font-bold mb-3 mt-5",
    h3: "text-xl font-bold mb-2 mt-4",
    h4: "text-lg font-semibold mb-2 mt-3",
    h5: "text-base font-semibold mb-1 mt-2",
  },
  list: {
    ul: "list-disc list-inside mb-2",
    ol: "list-decimal list-inside mb-2",
  },
  text: {
    bold: "font-bold",
    italic: "italic",
    underline: "underline",
    strikethrough: "line-through",
    code: "bg-gray-100 rounded px-1 py-0.5 font-mono text-sm",
  },
  link: "text-blue-600 underline hover:text-blue-800",
  code: "bg-gray-100 rounded p-2 font-mono text-sm block mb-2",
};

function onError(error: Error) {
  console.error("Lexical Error:", error);
}

// Plugin to convert HTML to Lexical nodes on mount
function HtmlConverterPlugin({ htmlContent }: { htmlContent?: string }) {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    if (!htmlContent) return;

    editor.update(() => {
      // Parse HTML
      const parser = new DOMParser();
      const dom = parser.parseFromString(htmlContent, "text/html");

      // Generate Lexical nodes from DOM
      const nodes = $generateNodesFromDOM(editor, dom);

      // Insert nodes into editor
      const root = $getRoot();
      root.clear();
      root.append(...nodes);
    });
  }, [editor, htmlContent]);

  return null;
}

export function LexicalEditor({
  initialContent,
  onChange,
  readOnly = false,
  placeholder = "Start typing your contract...",
  yjsProviders = null,
  enableCollaboration = false,
}: LexicalEditorProps) {
  // Check if content is HTML (from DOCX import)
  const isHtml = initialContent?.startsWith('__HTML__');
  const htmlContent = isHtml ? initialContent?.substring(8) : undefined;
  const lexicalContent = isHtml ? undefined : initialContent;

  // Don't use initialContent if collaboration is enabled (Yjs handles state)
  const shouldUseInitialContent = !enableCollaboration && lexicalContent;

  const initialConfig = {
    namespace: "ContractEditor",
    theme,
    onError,
    editable: !readOnly,
    nodes: [
      HeadingNode,
      ListNode,
      ListItemNode,
      QuoteNode,
      CodeNode,
      AutoLinkNode,
      LinkNode,
      TableNode,
      TableCellNode,
      TableRowNode,
    ],
    editorState: shouldUseInitialContent && shouldUseInitialContent.trim() !== "" ? shouldUseInitialContent : undefined,
  };

  const handleChange = (editorState: EditorState) => {
    if (onChange) {
      editorState.read(() => {
        const json = JSON.stringify(editorState.toJSON());
        onChange(json);
      });
    }
  };

  return (
    <LexicalComposer initialConfig={initialConfig}>
      <div className="relative border rounded-lg bg-white overflow-hidden">
        {!readOnly && <EditorToolbar />}
        <div className="relative">
          <RichTextPlugin
            contentEditable={
              <ContentEditable
                className="min-h-[500px] max-h-[800px] overflow-y-auto px-6 py-4 focus:outline-none prose prose-sm max-w-none"
                aria-placeholder={placeholder}
                placeholder={
                  <div className="absolute top-4 left-6 text-gray-400 pointer-events-none select-none">
                    {placeholder}
                  </div>
                }
              />
            }
            placeholder={null}
            ErrorBoundary={() => <div>An error occurred</div>}
          />
        </div>
        <HistoryPlugin />
        <OnChangePlugin onChange={handleChange} />
        <TablePlugin />
        {enableCollaboration && yjsProviders && (
          <CollaborationPlugin
            providers={yjsProviders}
            shouldBootstrap={!shouldUseInitialContent}
          />
        )}
        {isHtml && htmlContent && <HtmlConverterPlugin htmlContent={htmlContent} />}
      </div>
    </LexicalComposer>
  );
}
