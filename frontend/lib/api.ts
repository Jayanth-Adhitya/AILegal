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
  async uploadPolicy(file: File): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post<UploadResponse>(
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
  async uploadPolicies(files: File[]): Promise<UploadResponse[]> {
    const uploads = files.map((file) => this.uploadPolicy(file));
    return Promise.all(uploads);
  },

  // Get all policies
  async getPolicies(): Promise<Policy[]> {
    try {
      const response = await api.get<{ success: boolean; policies: Policy[]; total_chunks: number; company_id: string }>("/api/policies");
      return response.data.policies;
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
