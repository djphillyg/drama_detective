import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { SessionState, SessionStatus } from '@/lib/types';

const initialState: SessionState = {
  sessionId: null,
  incidentName: '',
  status: 'idle',
  error: null,
};

const sessionSlice = createSlice({
  name: 'session',
  initialState,
  reducers: {
    setSessionId: (state, action: PayloadAction<string>) => {
      state.sessionId = action.payload;
    },
    setIncidentName: (state, action: PayloadAction<string>) => {
      state.incidentName = action.payload;
    },
    setStatus: (state, action: PayloadAction<SessionStatus>) => {
      state.status = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      if (action.payload) {
        state.status = 'error';
      }
    },
    resetSession: () => initialState,
  },
});

export const {
  setSessionId,
  setIncidentName,
  setStatus,
  setError,
  resetSession
} = sessionSlice.actions;

export default sessionSlice.reducer;
