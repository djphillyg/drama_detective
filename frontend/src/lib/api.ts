import {
  InvestigateResponse,
  AnswerResponse,
  AnalysisResponse,
  Answer
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// JWT token management
const TOKEN_KEY = 'drama_detective_token';

export const tokenManager = {
  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem(TOKEN_KEY);
    }
    return null;
  },

  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(TOKEN_KEY, token);
    }
  },

  clearToken(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem(TOKEN_KEY);
    }
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  }
};

async function fetchWithErrorHandling(url: string, options: RequestInit) {
  // Add JWT token to headers if available
  const token = tokenManager.getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new ApiError(response.status, errorData.error || 'Request failed');
  }

  return response.json();
}

export const api = {
  async verifyPassword(password: string): Promise<{ success: boolean; token: string }> {
    const response = await fetchWithErrorHandling(`${API_BASE}/verify-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });

    // Store the token
    if (response.token) {
      tokenManager.setToken(response.token);
    }

    return response;
  },

  async investigate(
    incidentName: string,
    summary: string,
    intervieweeName?: string,
    relationship?: string,
    images?: string[],
    confidenceThreshold?: number
  ): Promise<InvestigateResponse> {
    return fetchWithErrorHandling(`${API_BASE}/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        incident_name: incidentName,
        summary,
        interviewee_name: intervieweeName,
        interviewee_role: relationship,
        images: images || [],
        confidence_threshold: confidenceThreshold
      }),
    });
  },

  async submitAnswer(sessionId: string, answer: Answer): Promise<AnswerResponse> {
    return fetchWithErrorHandling(`${API_BASE}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        answer
      }),
    });
  },

  async getAnalysis(sessionId: string): Promise<AnalysisResponse> {
    return fetchWithErrorHandling(`${API_BASE}/analysis/${sessionId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
  },
};

export { ApiError };
