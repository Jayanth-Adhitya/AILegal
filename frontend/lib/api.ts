import axios, { AxiosError } from "axios";
import type {
  Policy,
  AnalysisResult,
  JobStatus,
  UploadResponse,
  ApiResponse,
  Negotiation,
  NegotiationMessage,
  CreateNegotiationRequest,
  NegotiationListResponse,
  MessageListResponse,
  Document,
  CreateDocumentRequest,
  UpdateDocumentRequest,
  DocumentListResponse,
  DocumentCollaborator,
  AddCollaboratorRequest,
} from "./types";

// Get API URL from environment variable with fallback
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Export for use in other components
export const API_BASE_URL = API_URL;

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Enable sending cookies with requests
});

// Error handling helper
function handleApiError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    const message =
      axiosError.response?.data?.detail ||
      axiosError.response?.data?.message ||
      axiosError.message ||
      "An unexpected error occurred";
    throw new Error(message);
  }
  throw error;
}

// Policy API
export const policyApi = {
  // Upload single policy file
  async uploadPolicy(file: File): Promise<{ success: boolean; policy: Policy; parsing_status: string; message: string }> {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post<{ success: boolean; policy: Policy; parsing_status: string; message: string }>(
        "/api/policies/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Upload multiple policy files
  async uploadPolicies(files: File[]): Promise<{ success: boolean; policy: Policy; parsing_status: string; message: string }[]> {
    const uploads = files.map((file) => this.uploadPolicy(file));
    return Promise.all(uploads);
  },

  // Get all policies
  async getPolicies(params?: { status?: string; search?: string }): Promise<Policy[]> {
    try {
      const response = await api.get<{ success: boolean; policies: Policy[]; total: number }>("/api/policies", { params });
      return response.data.policies;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Get single policy by ID
  async getPolicy(policyId: string): Promise<Policy> {
    try {
      const response = await api.get<{ success: boolean; policy: Policy }>(`/api/policies/${policyId}`);
      return response.data.policy;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Update policy
  async updatePolicy(policyId: string, updateData: any): Promise<Policy> {
    try {
      const response = await api.put<{ success: boolean; policy: Policy; message: string }>(
        `/api/policies/${policyId}`,
        updateData
      );
      return response.data.policy;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Delete policy
  async deletePolicy(policyId: string): Promise<void> {
    try {
      await api.delete(`/api/policies/${policyId}`);
    } catch (error) {
      handleApiError(error);
    }
  },

  // Reingest policies (rebuild vector store)
  async reingestPolicies(): Promise<{ message: string }> {
    try {
      const response = await api.post<{ message: string }>(
        "/api/policies/reingest"
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Send chat message to policy chatbot
  async sendChatMessage(
    policyId: string,
    message: string,
    conversationHistory?: Array<{ role: string; content: string }>
  ): Promise<{ response: string; policy_id: string; timestamp: string }> {
    try {
      const response = await api.post<{ response: string; policy_id: string; timestamp: string }>(
        `/api/policies/${policyId}/chat`,
        {
          message,
          conversation_history: conversationHistory || [],
        }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

// Contract Analysis API
export const contractApi = {
  // Upload contract for analysis
  async uploadContract(file: File): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post<UploadResponse>(
        "/api/contracts/upload",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Start contract analysis
  async analyzeContract(
    jobId: string
  ): Promise<{ job_id: string; status: string; message: string }> {
    try {
      const response = await api.post<{ job_id: string; status: string; message: string }>(
        `/api/contracts/${jobId}/analyze`
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Get analysis job status
  async getJobStatus(jobId: string): Promise<JobStatus> {
    try {
      const response = await api.get<JobStatus>(
        `/api/contracts/${jobId}/status`
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Download analysis report
  async downloadReport(
    jobId: string,
    reportType: "reviewed" | "detailed" | "html"
  ): Promise<Blob> {
    try {
      const response = await api.get(
        `/api/contracts/${jobId}/download/${reportType}`,
        {
          responseType: "blob",
        }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Cancel analysis job
  async cancelJob(jobId: string): Promise<{ message: string }> {
    try {
      const response = await api.post<{ message: string }>(
        `/api/contracts/cancel/${jobId}`
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

// Chat API
export const chatApi = {
  // Send chat message with streaming response
  async sendMessage(
    jobId: string,
    message: string,
    history: Array<{ role: string; content: string }>
  ): Promise<Response> {
    const response = await fetch(`${API_URL}/api/chat/${jobId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include", // Enable sending cookies with request
      body: JSON.stringify({
        message,
        history,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to send message");
    }

    return response;
  },
};

// Voice API
export const voiceApi = {
  // Text to Speech
  async textToSpeech(
    text: string,
    voice?: string,
    model: string = "playai-tts"
  ): Promise<Blob> {
    try {
      const response = await api.post(
        "/api/voice/synthesize",
        {
          text,
          voice,
          model,
        },
        {
          responseType: "blob",
        }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Speech to Text
  async speechToText(formData: FormData): Promise<{
    status: string;
    transcription: string;
    language: string;
  }> {
    try {
      const response = await api.post("/api/voice/transcribe", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Get available voices
  async getVoices(language: string = "english"): Promise<{
    status: string;
    language: string;
    voices: string[];
    default: string | null;
  }> {
    try {
      const response = await api.get("/api/voice/voices", {
        params: { language },
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

// Negotiation API
export const negotiationApi = {
  // Create a new negotiation request
  async createNegotiation(request: CreateNegotiationRequest): Promise<Negotiation> {
    try {
      const response = await api.post<Negotiation>("/api/negotiations", request);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // List user's negotiations
  async listNegotiations(
    status?: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<NegotiationListResponse> {
    try {
      const response = await api.get<NegotiationListResponse>("/api/negotiations", {
        params: { status, limit, offset },
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Get negotiation details
  async getNegotiation(negotiationId: string): Promise<Negotiation> {
    try {
      const response = await api.get<Negotiation>(`/api/negotiations/${negotiationId}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Accept negotiation request
  async acceptNegotiation(negotiationId: string): Promise<Negotiation> {
    try {
      const response = await api.patch<Negotiation>(
        `/api/negotiations/${negotiationId}/accept`
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Reject negotiation request
  async rejectNegotiation(negotiationId: string, reason?: string): Promise<void> {
    try {
      await api.patch(`/api/negotiations/${negotiationId}/reject`, { reason });
    } catch (error) {
      handleApiError(error);
    }
  },

  // Mark negotiation as completed
  async completeNegotiation(negotiationId: string): Promise<void> {
    try {
      await api.patch(`/api/negotiations/${negotiationId}/complete`);
    } catch (error) {
      handleApiError(error);
    }
  },

  // Cancel negotiation
  async cancelNegotiation(negotiationId: string, reason?: string): Promise<void> {
    try {
      await api.delete(`/api/negotiations/${negotiationId}`, {
        data: { reason },
      });
    } catch (error) {
      handleApiError(error);
    }
  },

  // Send message (HTTP fallback)
  async sendMessage(
    negotiationId: string,
    content: string
  ): Promise<NegotiationMessage> {
    try {
      const response = await api.post<NegotiationMessage>(
        `/api/negotiations/${negotiationId}/messages`,
        { content, message_type: "text" }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Get message history
  async getMessages(
    negotiationId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<MessageListResponse> {
    try {
      const response = await api.get<MessageListResponse>(
        `/api/negotiations/${negotiationId}/messages`,
        { params: { limit, offset } }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Mark messages as read
  async markMessagesRead(
    negotiationId: string,
    messageIds: string[]
  ): Promise<void> {
    try {
      await api.patch(`/api/negotiations/${negotiationId}/messages/read`, {
        message_ids: messageIds,
      });
    } catch (error) {
      handleApiError(error);
    }
  },
};

// Document API
export const documentApi = {
  // Create a new document
  async createDocument(
    request: CreateDocumentRequest
  ): Promise<Document> {
    try {
      const response = await api.post<Document>("/api/documents", request);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Get all user's documents
  async listDocuments(
    limit: number = 50,
    offset: number = 0
  ): Promise<DocumentListResponse> {
    try {
      const response = await api.get<DocumentListResponse>("/api/documents", {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Get document by ID
  async getDocument(documentId: string): Promise<Document> {
    try {
      const response = await api.get<Document>(`/api/documents/${documentId}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Update document
  async updateDocument(
    documentId: string,
    request: UpdateDocumentRequest
  ): Promise<Document> {
    try {
      const response = await api.patch<Document>(
        `/api/documents/${documentId}`,
        request
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Delete document
  async deleteDocument(documentId: string): Promise<void> {
    try {
      await api.delete(`/api/documents/${documentId}`);
    } catch (error) {
      handleApiError(error);
    }
  },

  // Get collaborators for a document
  async getCollaborators(
    documentId: string
  ): Promise<DocumentCollaborator[]> {
    try {
      const response = await api.get<{ collaborators: DocumentCollaborator[] }>(
        `/api/documents/${documentId}/collaborators`
      );
      return response.data.collaborators;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Add collaborator to a document
  async addCollaborator(
    documentId: string,
    request: AddCollaboratorRequest
  ): Promise<DocumentCollaborator> {
    try {
      const response = await api.post<{ success: boolean; collaborator: DocumentCollaborator }>(
        `/api/documents/${documentId}/collaborators`,
        request
      );
      return response.data.collaborator;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Import DOCX file
  async importDocx(
    file: File,
    options?: {
      title?: string;
      importSource?: "original" | "ai_redlined";
      negotiationId?: string;
      analysisJobId?: string;
    }
  ): Promise<{
    success: boolean;
    document_id: string;
    html: string;
    track_changes: any[];
    metadata: any;
  }> {
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (options?.title) formData.append("title", options.title);
      if (options?.importSource) formData.append("import_source", options.importSource);
      if (options?.negotiationId) formData.append("negotiation_id", options.negotiationId);
      if (options?.analysisJobId) formData.append("analysis_job_id", options.analysisJobId);

      const response = await api.post("/api/documents/import-docx", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Download original DOCX file
  async downloadOriginal(documentId: string): Promise<Blob> {
    try {
      const response = await api.get(`/api/documents/${documentId}/original`, {
        responseType: "blob",
      });
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Update document content with DOCX file (for SuperDoc)
  async updateDocumentContent(
    documentId: string,
    formData: FormData
  ): Promise<Document> {
    try {
      const response = await api.post<Document>(
        `/api/documents/${documentId}/content`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Get track changes for a document
  async getTrackChanges(documentId: string): Promise<any[]> {
    try {
      const response = await api.get<{ success: boolean; changes: any[] }>(
        `/api/documents/${documentId}/track-changes`
      );
      return response.data.changes;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Check if Y.js collaboration state exists for a document
  async hasCollaborationState(documentId: string): Promise<boolean> {
    try {
      const response = await api.get<{ document_id: string; state: string | null }>(
        `/api/documents/${documentId}/yjs-state`
      );
      // State exists if it's a non-empty string longer than 10 chars (minimal Y.js state)
      return !!(response.data.state && response.data.state.length > 10);
    } catch (error) {
      // If error, assume no state exists
      return false;
    }
  },

  // Enable collaboration for a document
  async enableCollaboration(documentId: string): Promise<{ status: string }> {
    try {
      const response = await api.post<{ document_id: string; status: string }>(
        `/api/documents/${documentId}/enable-collaboration`
      );
      return { status: response.data.status };
    } catch (error) {
      handleApiError(error);
    }
  },

  // Approve document
  async approveDocument(documentId: string): Promise<{ success: boolean; document_id: string; status: string }> {
    try {
      const response = await api.post<{ success: boolean; document_id: string; status: string }>(
        `/api/documents/${documentId}/approve`
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Reject document
  async rejectDocument(documentId: string, reason: string): Promise<{ success: boolean; document_id: string; status: string }> {
    try {
      const response = await api.post<{ success: boolean; document_id: string; status: string }>(
        `/api/documents/${documentId}/reject`,
        { reason }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  // Sign document
  async signDocument(
    documentId: string,
    signatureData: { signature_data: string; signature_type: "drawn" | "typed"; signer_name: string }
  ): Promise<{ success: boolean; signature_id: string }> {
    try {
      const response = await api.post<{ success: boolean; signature_id: string }>(
        `/api/documents/${documentId}/sign`,
        signatureData
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

// Health check
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await api.get("/health");
    return response.status === 200;
  } catch (error) {
    return false;
  }
}

export default api;
