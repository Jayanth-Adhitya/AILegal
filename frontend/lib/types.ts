// Policy Types
export interface Policy {
  id: string;
  name: string;
  type: string;
  version: string;
  file_path: string;
  uploaded_at: string;
  file_size?: number;
}

// Contract Analysis Types
export interface IssueObject {
  issue_description: string;
  policy_reference?: string;
  severity?: string;
}

export interface RecommendationObject {
  recommendation: string;
  [key: string]: any;
}

export interface PolicyReferenceObject {
  policy_name?: string;
  [key: string]: any;
}

export interface ClauseAnalysis {
  clause_number: number;
  clause_text: string;
  clause_type: string;
  compliance_status: "Compliant" | "Non-Compliant" | "Needs Review";
  issues: (string | IssueObject)[];
  recommendations: (string | RecommendationObject)[];
  policy_references: (string | PolicyReferenceObject)[];
  risk_level: "Low" | "Medium" | "High" | "Critical";
  suggested_text?: string;
}

export interface AnalysisSummary {
  total_clauses: number;
  compliant_clauses: number;
  non_compliant_clauses: number;
  needs_review_clauses: number;
  critical_issues: number;
  high_risk_issues: number;
  medium_risk_issues: number;
  low_risk_issues: number;
  compliance_rate: number;
  overall_risk: "Low" | "Medium" | "High" | "Critical";
}

export interface AnalysisResult {
  job_id: string;
  contract_name: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress?: number;
  current_clause?: number;
  total_clauses?: number;
  analysis_results?: ClauseAnalysis[];
  summary?: AnalysisSummary;
  output_files?: {
    reviewed_contract?: string;
    detailed_report?: string;
    html_summary?: string;
  };
  created_at: string;
  completed_at?: string;
  error?: string;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface UploadResponse {
  job_id: string;
  status: string;
  message: string;
  filename?: string;
  upload_path?: string;
}

export interface JobStatus {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  message?: string;
  result?: AnalysisResult;
}

// Filter Types
export type ClauseFilter = "all" | "non-compliant" | "critical";
export type RiskFilter = "all" | "low" | "medium" | "high" | "critical";
