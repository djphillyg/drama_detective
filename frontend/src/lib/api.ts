import {
  InvestigateResponse,
  AnswerResponse,
  AnalysisResponse,
  Answer
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchWithErrorHandling(url: string, options: RequestInit) {
  const response = await fetch(url, options);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new ApiError(response.status, errorData.error || 'Request failed');
  }

  return response.json();
}

export const api = {
  async investigate(incidentName: string, summary: string): Promise<InvestigateResponse> {
    return fetchWithErrorHandling(`${API_BASE}/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        incident_name: incidentName,
        summary
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
