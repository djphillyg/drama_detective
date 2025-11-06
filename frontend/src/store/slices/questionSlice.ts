import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { QuestionState, Answer } from '@/lib/types';

const initialState: QuestionState = {
  currentQuestion: '',
  answerOptions: [],
  selectedAnswerIndex: null,
  customAnswer: '',
  isSubmitting: false,
};

const questionSlice = createSlice({
  name: 'question',
  initialState,
  reducers: {
    setQuestion: (state, action: PayloadAction<{ question: string; answers: Answer[] }>) => {
      state.currentQuestion = action.payload.question;
      state.answerOptions = action.payload.answers;
      state.selectedAnswerIndex = null;
      state.customAnswer = '';
    },
    selectAnswer: (state, action: PayloadAction<number>) => {
      state.selectedAnswerIndex = action.payload;
      state.customAnswer = ''; // Clear custom answer when selecting pre-gen
    },
    setCustomAnswer: (state, action: PayloadAction<string>) => {
      state.customAnswer = action.payload;
      // Clear selected answer when user enters custom text
      console.log(state.customAnswer.trim().length)
      if (action.payload.trim().length > 0) {
        state.selectedAnswerIndex = null;
      }
    },
    setIsSubmitting: (state, action: PayloadAction<boolean>) => {
      state.isSubmitting = action.payload;
    },
    resetQuestion: () => initialState,
  },
});

export const {
  setQuestion,
  selectAnswer,
  setCustomAnswer,
  setIsSubmitting,
  resetQuestion
} = questionSlice.actions;

export default questionSlice.reducer;
