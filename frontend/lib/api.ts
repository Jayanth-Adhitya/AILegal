import axios, { AxiosError } from "axios";
import type {
  Policy,
  AnalysisResult,
  JobStatus,
  UploadResponse,
  ApiResponse,
} from "./types";

// Get API URL from environment variable with fallback
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
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
      const response = await api.get<Policy[]>("/api/policies");
      return response.data;
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
