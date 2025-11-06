import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ProgressState, Goal } from '@/lib/types';

const initialState: ProgressState = {
  turnCount: 0,
  goals: [],
  factsCount: 0,
};

const progressSlice = createSlice({
  name: 'progress',
  initialState,
  reducers: {
    updateProgress: (
      state,
      action: PayloadAction<{
        turnCount?: number;
        goals?: Goal[];
        factsCount?: number
      }>
    ) => {
      console.log(action.payload)
      if (action.payload.turnCount !== undefined) {
        state.turnCount = action.payload.turnCount;
      }
      if (action.payload.goals !== undefined) {
        state.goals = action.payload.goals;
      }
      if (action.payload.factsCount !== undefined) {
        state.factsCount = action.payload.factsCount;
      }
    },
    resetProgress: () => initialState,
  },
});

export const { updateProgress, resetProgress } = progressSlice.actions;

export default progressSlice.reducer;
