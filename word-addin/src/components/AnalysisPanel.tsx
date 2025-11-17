import React, { useState } from 'react';
import {
  makeStyles,
  tokens,
  Text,
  Button,
  Spinner,
  Card,
  CardHeader,
  Badge,
  Divider,
} from '@fluentui/react-components';
import {
  DocumentSearch24Regular,
  CheckmarkCircle24Regular,
  ErrorCircle24Regular,
  Warning24Regular,
} from '@fluentui/react-icons';
import { User, AnalysisResult, ClauseAnalysis } from '../types/analysis';
import { wordAPI } from '../services/word-api';
import { backendAPI } from '../services/backend-api';
import ClauseCard from './ClauseCard';
import SummaryStats from './SummaryStats';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalM,
  },
  analyzeButton: {
    width: '100%',
  },
  resultsContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalS,
  },
  sectionTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
    marginBottom: tokens.spacingVerticalS,
  },
  noResults: {
    textAlign: 'center',
    padding: tokens.spacingVerticalL,
    color: tokens.colorNeutralForeground3,
  },
  batchActions: {
    display: 'flex',
    gap: tokens.spacingHorizontalS,
    marginTop: tokens.spacingVerticalS,
  },
});

interface AnalysisPanelProps {
  user: User;
  analysisResult: AnalysisResult | null;
  isAnalyzing: boolean;
  onAnalysisStart: () => void;
  onAnalysisComplete: (result: AnalysisResult) => void;
  onError: (error: string) => void;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  analysisResult,
  isAnalyzing,
  onAnalysisStart,
  onAnalysisComplete,
  onError,
}) => {
  const styles = useStyles();
  const [selectedClauses, setSelectedClauses] = useState<Set<number>>(new Set());

  const handleAnalyzeDocument = async () => {
    onAnalysisStart();

    try {
      // Extract document content
      const paragraphs = await wordAPI.getParagraphs();

      if (paragraphs.length === 0) {
        onError('No content found in document. Please ensure the document contains text.');
        return;
      }

      const documentText = paragraphs.map((p) => p.text).join('\n\n');
      const paragraphTexts = paragraphs.map((p) => p.text);
      const paragraphIndices = paragraphs.map((p) => p.index);

      // Send to backend for analysis
      const result = await backendAPI.analyzeText({
        document_text: documentText,
        paragraphs: paragraphTexts,
        paragraph_indices: paragraphIndices,
      });

      onAnalysisComplete(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Analysis failed';
      onError(message);
    }
  };

  const handleNavigateToClause = async (clause: ClauseAnalysis) => {
    try {
      await wordAPI.scrollToParagraph(clause.paragraph_index);
    } catch (error) {
      onError('Failed to navigate to clause');
    }
  };

  const handleAddComment = async (clause: ClauseAnalysis) => {
    try {
      await wordAPI.addComplianceComment(
        clause.paragraph_index,
        clause.risk_level,
        clause.issues,
        clause.recommendations,
        clause.policy_references
      );
    } catch (error) {
      onError('Failed to add comment');
    }
  };

  const handleApplySuggestion = async (clause: ClauseAnalysis) => {
    if (!clause.suggested_text) {
      onError('No suggestion available for this clause');
      return;
    }

    try {
      const success = await wordAPI.replaceClauseText(
        clause.paragraph_index,
        clause.clause_text,
        clause.suggested_text
      );
      if (!success) {
        onError('Failed to apply suggestion: paragraph not found');
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      console.error('Apply suggestion error:', errorMsg);
      onError(`Failed to apply suggestion: ${errorMsg}`);
    }
  };

  const handleSelectClause = (clauseNumber: number, selected: boolean) => {
    setSelectedClauses((prev) => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(clauseNumber);
      } else {
        newSet.delete(clauseNumber);
      }
      return newSet;
    });
  };

  const handleApplyAllSuggestions = async () => {
    if (!analysisResult) return;

    const clausesToApply = analysisResult.analysis_results.filter(
      (c) => selectedClauses.has(c.clause_number) && c.suggested_text
    );

    if (clausesToApply.length === 0) {
      onError('No clauses with suggestions selected');
      return;
    }

    try {
      const suggestions = clausesToApply.map((c) => ({
        paragraphIndex: c.paragraph_index,
        originalText: c.clause_text,
        newText: c.suggested_text!,
      }));

      const result = await wordAPI.batchApplySuggestions(suggestions);

      if (result.failed > 0) {
        onError(`Applied ${result.success} suggestions, ${result.failed} failed`);
      }
    } catch (error) {
      onError('Failed to apply suggestions');
    }
  };

  const nonCompliantClauses = analysisResult?.analysis_results.filter(
    (c) => c.compliance_status === 'Non-Compliant'
  ) || [];

  const compliantClauses = analysisResult?.analysis_results.filter(
    (c) => c.compliance_status === 'Compliant'
  ) || [];

  return (
    <div className={styles.container}>
      <Button
        className={styles.analyzeButton}
        appearance="primary"
        icon={isAnalyzing ? <Spinner size="tiny" /> : <DocumentSearch24Regular />}
        onClick={handleAnalyzeDocument}
        disabled={isAnalyzing}
        size="large"
      >
        {isAnalyzing ? 'Analyzing Document...' : 'Analyze Document'}
      </Button>

      {analysisResult && (
        <>
          <SummaryStats summary={analysisResult.summary} />

          <Divider />

          {nonCompliantClauses.length > 0 && (
            <div className={styles.resultsContainer}>
              <div className={styles.sectionTitle}>
                <ErrorCircle24Regular color={tokens.colorPaletteRedForeground1} />
                <Text weight="semibold" size={400}>
                  Non-Compliant Clauses
                </Text>
                <Badge appearance="filled" color="danger">
                  {nonCompliantClauses.length}
                </Badge>
              </div>

              {nonCompliantClauses.map((clause) => (
                <ClauseCard
                  key={clause.clause_number}
                  clause={clause}
                  selected={selectedClauses.has(clause.clause_number)}
                  onSelect={(selected) => handleSelectClause(clause.clause_number, selected)}
                  onNavigate={() => handleNavigateToClause(clause)}
                  onAddComment={() => handleAddComment(clause)}
                  onApplySuggestion={() => handleApplySuggestion(clause)}
                />
              ))}

              <div className={styles.batchActions}>
                <Button
                  appearance="primary"
                  onClick={handleApplyAllSuggestions}
                  disabled={selectedClauses.size === 0}
                >
                  Apply Selected Suggestions ({selectedClauses.size})
                </Button>
              </div>
            </div>
          )}

          {compliantClauses.length > 0 && (
            <div className={styles.resultsContainer}>
              <div className={styles.sectionTitle}>
                <CheckmarkCircle24Regular color={tokens.colorPaletteGreenForeground1} />
                <Text weight="semibold" size={400}>
                  Compliant Clauses
                </Text>
                <Badge appearance="filled" color="success">
                  {compliantClauses.length}
                </Badge>
              </div>

              {compliantClauses.slice(0, 5).map((clause) => (
                <ClauseCard
                  key={clause.clause_number}
                  clause={clause}
                  selected={false}
                  onNavigate={() => handleNavigateToClause(clause)}
                  compact
                />
              ))}

              {compliantClauses.length > 5 && (
                <Text size={200} className={styles.noResults}>
                  ... and {compliantClauses.length - 5} more compliant clauses
                </Text>
              )}
            </div>
          )}
        </>
      )}

      {!analysisResult && !isAnalyzing && (
        <Card>
          <CardHeader
            header={
              <Text weight="semibold">Ready to Analyze</Text>
            }
            description="Click 'Analyze Document' to scan your contract for compliance issues, risks, and get AI-powered suggestions."
          />
        </Card>
      )}
    </div>
  );
};

export default AnalysisPanel;
