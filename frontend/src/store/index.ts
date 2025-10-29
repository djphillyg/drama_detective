import { configureStore } from '@reduxjs/toolkit';
import sessionReducer from './slices/sessionSlice';
import questionReducer from './slices/questionSlice';
import progressReducer from './slices/progressSlice';
import analysisReducer from './slices/analysisSlice';

export const makeStore = () => {
  return configureStore({
    reducer: {
      session: sessionReducer,
      question: questionReducer,
      progress: progressReducer,
      analysis: analysisReducer,
    },
  });
};

export type AppStore = ReturnType<typeof makeStore>;
export type RootState = ReturnType<AppStore['getState']>;
export type AppDispatch = AppStore['dispatch'];
