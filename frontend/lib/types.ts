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

// Chat Types
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface ChatHistory {
  role: string;
  content: string;
}

export interface ChatRequest {
  message: string;
  history: ChatHistory[];
}

export interface ChatResponse {
  content?: string;
  done?: boolean;
  error?: string;
}

// Voice Types
export interface TTSRequest {
  text: string;
  voice?: string;
  model?: string;
}

export interface STTResponse {
  status: string;
  transcription: string;
  language: string;
}

export interface VoicesResponse {
  status: string;
  language: string;
  voices: string[];
  default: string | null;
}

// Negotiation Types
export interface User {
  id: string;
  email: string;
  company_name: string;
  company_id: string;
  created_at: string;
}

export interface Negotiation {
  id: string;
  contract_name: string;
  contract_job_id?: string;
  initiator_user_id: string;
  receiver_user_id: string;
  status: "pending" | "active" | "completed" | "rejected" | "cancelled";
  created_at: string;
  accepted_at?: string;
  completed_at?: string;
  initiator?: User;
  receiver?: User;
  unread_count?: number;
}

export interface NegotiationMessage {
  id: string;
  negotiation_id: string;
  sender_user_id?: string;
  sender_type: "user" | "system";
  content: string;
  message_type: "text" | "system";
  created_at: string;
  read_at?: string;
  sender?: User;
}

export interface CreateNegotiationRequest {
  receiver_email: string;
  contract_name: string;
  contract_job_id?: string;
}

export interface NegotiationListResponse {
  success: boolean;
  negotiations: Negotiation[];
  total: number;
  limit: number;
  offset: number;
}

export interface MessageListResponse {
  success: boolean;
  messages: NegotiationMessage[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface WebSocketMessage {
  type: "message" | "typing" | "read" | "user_joined" | "user_left" | "ack" | "error";
  message_id?: string;
  user_id?: string;
  is_typing?: boolean;
  message_ids?: string[];
  reader_user_id?: string;
  code?: string;
  message?: string;
  timestamp?: string;
  // Message data
  id?: string;
  negotiation_id?: string;
  sender_user_id?: string;
  sender_type?: "user" | "system";
  content?: string;
  message_type?: "text" | "system";
  created_at?: string;
  read_at?: string;
  sender?: User;
}
