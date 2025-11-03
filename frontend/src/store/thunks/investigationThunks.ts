import { createAsyncThunk } from '@reduxjs/toolkit';
import { api, ApiError } from '@/lib/api';
import { Answer } from '@/lib/types';
import {
  setSessionId,
  setIncidentName,
  setStatus,
  setError
} from '../slices/sessionSlice';
import { setQuestion, setIsSubmitting } from '../slices/questionSlice';
import { updateProgress } from '../slices/progressSlice';
import {
  setAnalysisLoading,
  setAnalysisData
} from '../slices/analysisSlice';

export const startInvestigation = createAsyncThunk(
  'investigation/start',
  async (
    {
      incidentName,
      summary,
      intervieweeName,
      relationship
    }: {
      incidentName: string;
      summary: string;
      intervieweeName?: string;
      relationship?: string;
    },
    { dispatch, rejectWithValue }
  ) => {
    try {
      dispatch(setStatus('investigating'));

      const response = await api.investigate(incidentName, summary, intervieweeName, relationship);

      dispatch(setSessionId(response.session_id));
      dispatch(setIncidentName(response.incident_name));
      dispatch(setQuestion({
        question: response.question,
        answers: response.answers,
      }));
      dispatch(updateProgress({
        turnCount: response.turn_count,
        goals: response.goals,
      }));
      dispatch(setStatus('questioning'));

      return response;
    } catch (error) {
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to start investigation';
      dispatch(setError(message));
      return rejectWithValue(message);
    }
  }
);

export const submitAnswer = createAsyncThunk(
  'investigation/submitAnswer',
  async (
    { sessionId, answer }: { sessionId: string; answer: Answer },
    { dispatch, rejectWithValue }
  ) => {
    try {
      dispatch(setIsSubmitting(true));

      const response = await api.submitAnswer(sessionId, answer);

      dispatch(setIsSubmitting(false));

      if (response.is_complete) {
        dispatch(setStatus('complete'));
        return { isComplete: true };
      }

      if (response.question && response.answers) {
        dispatch(setQuestion({
          question: response.question,
          answers: response.answers,
        }));
        dispatch(updateProgress({
          turnCount: response.turn_count,
          goals: response.goals,
          factsCount: response.facts_count,
        }));
      }

      return { isComplete: false };
    } catch (error) {
      dispatch(setIsSubmitting(false));
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to submit answer';
      dispatch(setError(message));
      return rejectWithValue(message);
    }
  }
);

export const fetchAnalysis = createAsyncThunk(
  'investigation/fetchAnalysis',
  async (sessionId: string, { dispatch, rejectWithValue }) => {
    try {
      dispatch(setAnalysisLoading(true));
      dispatch(setStatus('analyzing'));

      const response = await api.getAnalysis(sessionId);

      dispatch(setAnalysisData(response.analysis));
      dispatch(setStatus('complete'));

      return response;
    } catch (error) {
      dispatch(setAnalysisLoading(false));
      const message = error instanceof ApiError
        ? error.message
        : 'Failed to fetch analysis';
      dispatch(setError(message));
      return rejectWithValue(message);
    }
  }
);
