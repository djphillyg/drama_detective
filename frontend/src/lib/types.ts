// Backend model types
export interface Answer {
  answer: string;
  reasoning: string;
}

export interface Goal {
  description: string;
  status: 'not_started' | 'in_progress' | 'complete';
  confidence: number; // 0-100
}

export interface Fact {
  topic: string;
  claim: string;
  source: string;
  timestamp: string | null;
  confidence: 'certain' | 'uncertain';
}

// API Response types
export interface InvestigateResponse {
  session_id: string;
  incident_name: string;
  question: string;
  answers: Answer[];
  turn_count: number;
  goals: Goal[];
}

export interface AnswerResponse {
  question?: string;
  answers?: Answer[];
  is_complete: boolean;
  turn_count?: number;
  goals?: Goal[];
  facts_count?: number;
  session_id?: string;
  message?: string;
}

export interface TimelineEvent {
  time: string;
  event: string;
}

export interface Verdict {
  primary_responsibility: string;
  percentage: number;
  reasoning: string;
  contributing_factors: string;
  drama_rating: number;
  drama_rating_explanation: string;
}

export interface AnalysisData {
  timeline: TimelineEvent[];
  key_facts: string[];
  gaps: string[];
  verdict: Verdict;
}

export interface AnalysisResponse {
  incident_name: string;
  analysis: AnalysisData;
}

// Frontend state types
export type SessionStatus =
  | 'idle'
  | 'investigating'
  | 'questioning'
  | 'analyzing'
  | 'complete'
  | 'error';

export interface SessionState {
  sessionId: string | null;
  incidentName: string;
  status: SessionStatus;
  error: string | null;
}

export interface QuestionState {
  currentQuestion: string;
  answerOptions: Answer[];
  selectedAnswerIndex: number | null;
  customAnswer: string;
  isSubmitting: boolean;
}

export interface ProgressState {
  turnCount: number;
  goals: Goal[];
  factsCount: number;
}

export interface AnalysisState {
  data: AnalysisData | null;
  isLoading: boolean;
  loadingMessage: string;
}
