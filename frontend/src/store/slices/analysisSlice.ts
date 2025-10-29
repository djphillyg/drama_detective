import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AnalysisState } from '@/lib/types';
import { getRandomLoadingMessage } from '@/lib/utils/loadingMessages';

const initialState: AnalysisState = {
  data: null,
  isLoading: false,
  loadingMessage: '',
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setAnalysisLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
      if (action.payload) {
        state.loadingMessage = getRandomLoadingMessage();
      }
    },
    setAnalysisData: (state, action: PayloadAction<string>) => {
      state.data = action.payload;
      state.isLoading = false;
    },
    updateLoadingMessage: (state) => {
      state.loadingMessage = getRandomLoadingMessage();
    },
    resetAnalysis: () => initialState,
  },
});

export const {
  setAnalysisLoading,
  setAnalysisData,
  updateLoadingMessage,
  resetAnalysis
} = analysisSlice.actions;

export default analysisSlice.reducer;
