/**
 * Type definitions for AI Legal Assistant Word Add-in
 */

export interface User {
  id: string;
  email: string;
  company_name: string;
  company_id: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user?: User;
  error?: string;
}

export interface ClauseAnalysis {
  clause_number: number;
  clause_text: string;
  clause_type: string;
  paragraph_index: number;
  compliance_status: 'Compliant' | 'Non-Compliant';
  risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
  issues: string[];
  recommendations: string[];
  policy_references: string[];
  suggested_text?: string;
}

export interface AnalysisSummary {
  total_clauses: number;
  compliant_clauses: number;
  non_compliant_clauses: number;
  critical_issues: number;
  high_risk_issues: number;
  medium_risk_issues: number;
  low_risk_issues: number;
  compliance_rate: number;
  overall_risk: 'Low' | 'Medium' | 'High' | 'Critical';
}

export interface AnalysisResult {
  job_id: string;
  status: 'completed' | 'failed' | 'processing';
  analysis_results: ClauseAnalysis[];
  summary: AnalysisSummary;
  error?: string;
}

export interface ParagraphInfo {
  index: number;
  text: string;
}

export interface AnalyzeTextRequest {
  document_text: string;
  paragraphs: string[];
  paragraph_indices?: number[]; // Original Word paragraph indices
}

export interface AppState {
  isAuthenticated: boolean;
  user: User | null;
  isAnalyzing: boolean;
  analysisResult: AnalysisResult | null;
  selectedClause: ClauseAnalysis | null;
  error: string | null;
}

export type RiskLevel = 'Low' | 'Medium' | 'High' | 'Critical';
export type ComplianceStatus = 'Compliant' | 'Non-Compliant';
