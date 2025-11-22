/**
 * Backend API Client - Communication with FastAPI backend
 */

import {
  User,
  AuthResponse,
  AnalysisResult,
  AnalyzeTextRequest,
} from '../types/analysis';

const API_BASE_URL = 'https://word.contract.cirilla.ai';

class BackendAPIClient {
  private sessionToken: string | null = null;

  /**
   * Set the session token for authenticated requests
   */
  setSessionToken(token: string): void {
    this.sessionToken = token;
    // Store in Office roaming settings for persistence
    if (Office.context && Office.context.roamingSettings) {
      Office.context.roamingSettings.set('sessionToken', token);
      Office.context.roamingSettings.saveAsync();
    }
  }

  /**
   * Get stored session token
   */
  getSessionToken(): string | null {
    if (this.sessionToken) {
      return this.sessionToken;
    }

    // Try to load from Office roaming settings
    if (Office.context && Office.context.roamingSettings) {
      const token = Office.context.roamingSettings.get('sessionToken');
      if (token) {
        this.sessionToken = token;
        return token;
      }
    }

    return null;
  }

  /**
   * Clear session token (logout)
   */
  clearSessionToken(): void {
    this.sessionToken = null;
    if (Office.context && Office.context.roamingSettings) {
      Office.context.roamingSettings.remove('sessionToken');
      Office.context.roamingSettings.saveAsync();
    }
  }

  /**
   * Make authenticated API request
   */
  private async fetchWithAuth(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const token = this.getSessionToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
      credentials: 'include', // Include cookies for fallback
    });

    if (response.status === 401) {
      this.clearSessionToken();
      throw new Error('Session expired. Please sign in again.');
    }

    return response;
  }

  /**
   * Check if user is authenticated
   */
  async checkSession(): Promise<User | null> {
    try {
      const response = await this.fetchWithAuth('/api/auth/me');
      if (response.ok) {
        const data = await response.json();
        return data.user;
      }
      return null;
    } catch {
      return null;
    }
  }

  /**
   * Login user
   */
  async login(email: string, password: string): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
        credentials: 'include',
      });

      const data = await response.json();

      if (data.success && data.user) {
        // Store the session token for Bearer auth
        if (data.session_token) {
          this.setSessionToken(data.session_token);
        }
        return {
          success: true,
          message: 'Login successful',
          user: data.user,
        };
      }

      return {
        success: false,
        message: data.message || 'Login failed',
        error: data.error,
      };
    } catch (error) {
      return {
        success: false,
        message: 'Network error',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await this.fetchWithAuth('/api/auth/logout', { method: 'POST' });
    } finally {
      this.clearSessionToken();
    }
  }

  /**
   * Analyze document text (main analysis endpoint for add-in)
   */
  async analyzeText(request: AnalyzeTextRequest): Promise<AnalysisResult> {
    const response = await this.fetchWithAuth('/api/word-addin/analyze-text', {
      method: 'POST',
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Analysis failed: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Analyze a single clause
   */
  async analyzeClause(clauseText: string, clauseType?: string): Promise<unknown> {
    const response = await this.fetchWithAuth('/api/analyze/clause', {
      method: 'POST',
      body: JSON.stringify({
        clause_text: clauseText,
        clause_type: clauseType,
      }),
    });

    if (!response.ok) {
      throw new Error(`Clause analysis failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.result;
  }

  /**
   * Get user's policies
   */
  async getUserPolicies(): Promise<unknown[]> {
    const response = await this.fetchWithAuth('/api/policies');
    if (!response.ok) {
      throw new Error(`Failed to fetch policies: ${response.statusText}`);
    }

    const data = await response.json();
    return data.policies || [];
  }
}

export const backendAPI = new BackendAPIClient();
