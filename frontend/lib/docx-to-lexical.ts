/**
 * Utility for converting DOCX files to Lexical editor format.
 */

import mammoth from "mammoth";
import { LexicalEditor } from "lexical";
import { $generateNodesFromDOM } from "@lexical/html";
import { $getRoot, $insertNodes } from "lexical";

export interface DocxConversionResult {
  success: boolean;
  html?: string;
  error?: string;
}

/**
 * Convert DOCX file to HTML using mammoth.js
 */
export async function convertDocxToHtml(file: File): Promise<DocxConversionResult> {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const result = await mammoth.convertToHtml({ arrayBuffer });

    return {
      success: true,
      html: result.value,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to convert DOCX",
    };
  }
}

/**
 * Convert HTML string to Lexical editor nodes
 */
export function convertHtmlToLexical(editor: LexicalEditor, htmlString: string): void {
  editor.update(() => {
    // Parse HTML
    const parser = new DOMParser();
    const dom = parser.parseFromString(htmlString, "text/html");

    // Generate Lexical nodes from DOM
    const nodes = $generateNodesFromDOM(editor, dom);

    // Clear existing content and insert new nodes
    const root = $getRoot();
    root.clear();
    root.append(...nodes);
  });
}

/**
 * Convert DOCX file directly to Lexical editor state
 */
export async function importDocxToLexical(
  editor: LexicalEditor,
  file: File
): Promise<{ success: boolean; error?: string }> {
  try {
    // Convert DOCX to HTML
    const htmlResult = await convertDocxToHtml(file);

    if (!htmlResult.success || !htmlResult.html) {
      return {
        success: false,
        error: htmlResult.error || "Failed to convert DOCX to HTML",
      };
    }

    // Convert HTML to Lexical
    convertHtmlToLexical(editor, htmlResult.html);

    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to import DOCX",
    };
  }
}

/**
 * Convert HTML string from backend API to Lexical state JSON
 */
export function htmlToLexicalState(editor: LexicalEditor, htmlString: string): string {
  let stateJson = "";

  editor.update(() => {
    // Parse and insert HTML
    const parser = new DOMParser();
    const dom = parser.parseFromString(htmlString, "text/html");
    const nodes = $generateNodesFromDOM(editor, dom);

    const root = $getRoot();
    root.clear();
    root.append(...nodes);

    // Get the editor state as JSON
    const editorState = editor.getEditorState();
    stateJson = JSON.stringify(editorState.toJSON());
  });

  return stateJson;
}
