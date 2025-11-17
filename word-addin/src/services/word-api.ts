/**
 * Word API Service - Wrapper for Office JavaScript API operations
 */

import { ParagraphInfo } from '../types/analysis';

export class WordAPIService {
  /**
   * Check if Word API is available and meets minimum requirements
   */
  static isAvailable(): boolean {
    return typeof Office !== 'undefined' && Office.context && Office.context.requirements;
  }

  /**
   * Check if specific requirement set is supported
   */
  static isRequirementSetSupported(name: string, version: string): boolean {
    if (!this.isAvailable()) return false;
    return Office.context.requirements.isSetSupported(name, version);
  }

  /**
   * Get full document text
   */
  async getDocumentText(): Promise<string> {
    return Word.run(async (context) => {
      const body = context.document.body;
      body.load('text');
      await context.sync();
      return body.text;
    });
  }

  /**
   * Get all paragraphs with their text and indices
   */
  async getParagraphs(): Promise<ParagraphInfo[]> {
    return Word.run(async (context) => {
      const paragraphs = context.document.body.paragraphs;
      paragraphs.load('items');
      await context.sync();

      const paragraphInfos: ParagraphInfo[] = [];
      for (let i = 0; i < paragraphs.items.length; i++) {
        paragraphs.items[i].load('text');
      }
      await context.sync();

      for (let i = 0; i < paragraphs.items.length; i++) {
        const text = paragraphs.items[i].text.trim();
        if (text) {
          paragraphInfos.push({
            index: i,
            text: text,
          });
        }
      }

      return paragraphInfos;
    });
  }

  /**
   * Get currently selected text
   */
  async getSelectedText(): Promise<string> {
    return Word.run(async (context) => {
      const selection = context.document.getSelection();
      selection.load('text');
      await context.sync();
      return selection.text;
    });
  }

  /**
   * Scroll to and highlight a specific paragraph
   */
  async scrollToParagraph(paragraphIndex: number): Promise<void> {
    await Word.run(async (context) => {
      const paragraphs = context.document.body.paragraphs;
      paragraphs.load('items');
      await context.sync();

      if (paragraphIndex >= 0 && paragraphIndex < paragraphs.items.length) {
        const paragraph = paragraphs.items[paragraphIndex];
        paragraph.select();
        await context.sync();
      }
    });
  }

  /**
   * Enable track changes mode
   */
  async enableTrackChanges(): Promise<void> {
    await Word.run(async (context) => {
      // @ts-ignore - changeTrackingMode may not be in type definitions
      if (context.document.changeTrackingMode !== undefined) {
        // @ts-ignore
        context.document.changeTrackingMode = Word.ChangeTrackingMode.trackAll;
        await context.sync();
      }
    });
  }

  /**
   * Insert a comment on a specific paragraph
   */
  async addCommentToParagraph(
    paragraphIndex: number,
    commentText: string
  ): Promise<void> {
    await Word.run(async (context) => {
      const paragraphs = context.document.body.paragraphs;
      paragraphs.load('items');
      await context.sync();

      if (paragraphIndex >= 0 && paragraphIndex < paragraphs.items.length) {
        const paragraph = paragraphs.items[paragraphIndex];
        const range = paragraph.getRange();

        // @ts-ignore - insertComment may not be in older type definitions
        if (range.insertComment) {
          range.insertComment(commentText);
          await context.sync();
        }
      }
    });
  }

  /**
   * Replace text in a paragraph with suggested text (tracked change)
   */
  async replaceClauseText(
    paragraphIndex: number,
    originalText: string,
    newText: string
  ): Promise<boolean> {
    return Word.run(async (context) => {
      // Enable track changes first (requires WordApi 1.4+)
      // This will show changes as redlines in Word
      try {
        const doc = context.document as Word.Document & { changeTrackingMode?: Word.ChangeTrackingMode };
        if (doc.changeTrackingMode !== undefined) {
          doc.changeTrackingMode = Word.ChangeTrackingMode.trackAll;
          await context.sync();
        }
      } catch (e) {
        // Track changes may not be supported, continue anyway
        console.warn('Could not enable track changes:', e);
      }

      const paragraphs = context.document.body.paragraphs;
      paragraphs.load('items');
      await context.sync();

      if (paragraphIndex >= 0 && paragraphIndex < paragraphs.items.length) {
        const paragraph = paragraphs.items[paragraphIndex];
        paragraph.load('text');
        await context.sync();

        const paragraphText = paragraph.text.trim();
        const originalNormalized = originalText.trim();

        // Check if the paragraph text closely matches the original clause text
        // Use a similarity check - if paragraph starts with or contains significant portion of original
        const searchText = originalNormalized.substring(0, Math.min(50, originalNormalized.length));

        if (paragraphText.toLowerCase().includes(searchText.toLowerCase())) {
          // Found matching content, replace the entire paragraph
          paragraph.insertText(newText, Word.InsertLocation.replace);
          await context.sync();
          return true;
        } else {
          // Try searching within the document body around this area
          const range = paragraph.getRange();
          const searchResults = range.search(searchText, {
            matchWholeWord: false,
            matchCase: false,
          });
          searchResults.load('items');
          await context.sync();

          if (searchResults.items.length > 0) {
            // Replace the entire paragraph content, not just the search result
            paragraph.insertText(newText, Word.InsertLocation.replace);
            await context.sync();
            return true;
          } else {
            // Last resort: just replace the paragraph
            paragraph.insertText(newText, Word.InsertLocation.replace);
            await context.sync();
            return true;
          }
        }
      }

      return false;
    });
  }

  /**
   * Add a compliance review comment with issues and recommendations
   */
  async addComplianceComment(
    paragraphIndex: number,
    riskLevel: string,
    issues: string[],
    recommendations: string[],
    policyReferences: string[]
  ): Promise<void> {
    const commentParts = [
      `AI Compliance Review - ${riskLevel} Risk`,
      '',
      'Issues:',
      ...issues.map((issue) => `• ${issue}`),
    ];

    if (recommendations.length > 0) {
      commentParts.push('', 'Recommendations:', ...recommendations.map((rec) => `• ${rec}`));
    }

    if (policyReferences.length > 0) {
      commentParts.push('', 'Policy References:', ...policyReferences.map((ref) => `• ${ref}`));
    }

    const commentText = commentParts.join('\n');
    await this.addCommentToParagraph(paragraphIndex, commentText);
  }

  /**
   * Batch apply multiple suggestions as tracked changes
   */
  async batchApplySuggestions(
    suggestions: Array<{
      paragraphIndex: number;
      originalText: string;
      newText: string;
    }>
  ): Promise<{ success: number; failed: number }> {
    let success = 0;
    let failed = 0;

    for (const suggestion of suggestions) {
      try {
        const result = await this.replaceClauseText(
          suggestion.paragraphIndex,
          suggestion.originalText,
          suggestion.newText
        );
        if (result) {
          success++;
        } else {
          failed++;
        }
      } catch {
        failed++;
      }
    }

    return { success, failed };
  }
}

export const wordAPI = new WordAPIService();
